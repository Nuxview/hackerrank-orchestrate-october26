"""Content-backed multi-format observations. Extraction errors are never absence."""

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess

from facts import Fact, normalize
from inputs import InputError, evidence_path, timestamp
from sql_snapshot import read_snapshot
from transport import RUN_ID, RuntimeFailure

COLLECTIONS = {
    "customer_profiles": ("account_service","USER_PROFILE"),
    "profile_lookups": ("account_service","USER_PROFILE"),
    "customer_search_documents": ("search_service","SEARCH_INDEX_ENTRY"),
    "index_queries": ("search_service","SEARCH_INDEX_ENTRY"),
    "customer_analytics_reports": ("analytics_platform","ANALYTICS_PROFILE"),
    "customer_analytics_profiles": ("analytics_platform","ANALYTICS_PROFILE"),
    "profiles": ("analytics_platform","ANALYTICS_PROFILE"),
    "connector_configurations": ("integration_service","DATA_FLOW"),
    "connector_subscriptions": ("integration_service","DATA_FLOW"),
    "connectors": ("integration_service","DATA_FLOW"),
    "backup_catalog": ("backup_service","BACKUP_ARCHIVE"),
    "backup_restore_entries": ("backup_service","BACKUP_ARCHIVE"),
    "restore_entries": ("backup_service","BACKUP_ARCHIVE"),
    "customer_export_jobs": ("export_service","USER_EXPORT"),
    "customer_exports": ("export_service","USER_EXPORT"),
    "exports": ("export_service","USER_EXPORT"),
    "ticket_attachments": ("support_platform","SUPPORT_ATTACHMENT"),
    "support_conversations": ("support_platform","SUPPORT_MESSAGE"),
    "support_records": ("support_platform","SUPPORT_MESSAGE"),
    "tickets": ("support_platform","SUPPORT_MESSAGE"),
    "security_audit_events": ("security_service","SECURITY_AUDIT_LOG"),
    "security_audit_records": ("security_service","SECURITY_AUDIT_LOG"),
    "audit_records": ("security_service","SECURITY_AUDIT_LOG"),
    "retained_order_records": ("legal_service","LEGAL_HOLD_RECORD"),
    "deleted_customer_references": ("identity_service","ACCOUNT_TOMBSTONE"),
    "marketing_profiles": ("marketing_platform","MARKETING_PROFILE"),
    "analytics_profiles": ("analytics_platform","ANALYTICS_PROFILE"),
}
RESULTS = {"NOT_FOUND":"ABSENT", "FOUND":"PRESENT", "IDENTIFIABLE":"IDENTIFIABLE",
           "ANONYMIZED":"ANONYMIZED", "REDACTED":"REDACTED", "ACTIVE":"ACTIVE",
           "DISABLED":"DISABLED", "BLOCKED":"BLOCKED"}
EMAIL = r"[A-Za-z0-9_.+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
KEY_FIELDS = {"email":"email", "owner_email":"email", "customer_email":"email",
    "requester_email":"email", "uploaded_by":"email", "phone":"phone",
    "owner_phone":"phone", "requester_phone":"phone", "email_hash":"email_hash",
    "customer_reference":"user_id", "subject_ref":"user_id", "user_id":"user_id"}


def flatten(data):
    for key,value in data.items():
        if isinstance(value,dict):yield from flatten(value)
        elif not isinstance(value,list):yield key,value


def keys_from(data):
    keys=set()
    for key,value in flatten(data):
        if not isinstance(value,str) or not value or value in {"null","no direct identifier","[REDACTED]"}:
            continue
        field=KEY_FIELDS.get(key)
        if key in {"subject_reference","subject_selector","lookup_value","_lookup","lookup_key",
                   "correlation_key","matched_value","match_key","subject_key","scan_key","owner_key"}:
            field=("email" if re.fullmatch(EMAIL,value) else "email_hash" if re.fullmatch(r"[a-fA-F0-9]{64}",value)
                   else "user_id" if re.fullmatch(r"user_[A-Za-z0-9_-]+",value) else "phone" if re.fullmatch(r"\+?[\d ().-]{7,}",value) else None)
        if field:keys.add((field,normalize(field,value)))
        if key in {"message_text","message_excerpt","details"}:
            keys.update(("email",normalize("email",m)) for m in re.findall(EMAIL,value))
        if key in {"file_name","business_key","order_reference","_business_key"}:
            keys.add(("business_key",value))
        if key in {"source_resource_id","target_resource_id"}:keys.add(("resource",value))
    return tuple(sorted(keys))


def observed_state(category,data):
    for key in ["rows","total_hits","direct_identifiers","http_status","status_code"]:
        if key in data and (type(data[key]) is not int or data[key]<0):
            raise InputError("Observed counts/status codes must be genuine nonnegative integers")
    if data.get("result") in RESULTS and data.get("record_type"):
        return RESULTS[data["result"]]
    if category not in {"DATA_FLOW","BACKUP_ARCHIVE"} and (
            data.get("rows")==0 or data.get("http_status")==404 or data.get("status_code")==404):
        return "ABSENT"
    if category=="DATA_FLOW":
        enabled=data.get("enabled",data.get("connector_status",data.get("status")))
        if isinstance(enabled,str):
            enabled={"true":True,"yes":True,"enabled":True,"active":True,"running":True,
                     "false":False,"no":False,"disabled":False,"paused":False,"stopped":False}.get(enabled.casefold())
        return "ACTIVE" if enabled is True or type(enabled) is int and enabled==1 else "DISABLED" if enabled is False or type(enabled) is int and enabled==0 else "UNKNOWN"
    if category=="BACKUP_ARCHIVE":
        allowed=data.get("restore_allowed")
        if isinstance(allowed,str):allowed={"true":True,"yes":True,"allowed":True,"false":False,"no":False,"blocked":False}.get(allowed.casefold())
        return "ACTIVE" if allowed is True or type(allowed) is int and allowed==1 else "BLOCKED" if allowed is False or type(allowed) is int and allowed==0 else "UNKNOWN"
    if category in {"ANALYTICS_PROFILE","PRODUCT_TELEMETRY"}:
        attribution=[v for k,v in flatten(data) if k in set(KEY_FIELDS)|{"subject_reference"}]
        return "IDENTIFIABLE" if any(v not in {None,"","[REDACTED]"} for v in attribution) else "ANONYMIZED" if len(attribution)>=3 else "UNKNOWN"
    if category=="ACCOUNT_TOMBSTONE":
        if not all(k in data for k in ["name","email","phone","email_hash"]):return "UNKNOWN"
        return "IDENTIFIABLE" if any(data[k] not in {None,"","[REDACTED]"} for k in ["name","email","phone","email_hash"]) else "REDACTED"
    if category in {"SUPPORT_MESSAGE","EMAIL_DELIVERY_LOG"}:
        values=[v for k,v in flatten(data) if k in {"email","phone","name","requester_name","requester_email","requester_phone","message_text","message_excerpt"}]
        if any(isinstance(v,str) and v not in {"","[REDACTED]"} for v in values):return "IDENTIFIABLE"
        return "REDACTED" if values else "UNKNOWN"
    if category=="USER_PROFILE" and (data.get("status_code")==404 or data.get("rows")==0 or data.get("http_status")==404):return "ABSENT"
    if category=="SEARCH_INDEX_ENTRY" and (data.get("result")=="miss" or data.get("total_hits")==0):return "ABSENT"
    return "PRESENT"


class Extractor:
    def __init__(self,dataset,tables,jobs=None):
        self.dataset=Path(dataset)
        self.tables=tables
        self.jobs=jobs
        self.facts=[]
        self.ledger=[]

    def add(self,manifest,system,resource,category,payload,location,observed=None,snapshot=None,copy="service",kind="observation",state=None):
        captured=timestamp(manifest["captured_at"])
        snap=timestamp(snapshot) if isinstance(snapshot,str) else snapshot or captured
        when=timestamp(observed) if isinstance(observed,str) else observed or snap
        data=dict(payload)
        data["_state"]=state or observed_state(category,data)
        data["_copy"]=copy
        self.facts.append(Fact(f'{manifest["file_id"]}:{len(self.facts)}',manifest["file_id"],manifest["file_path"],location,
            kind,system,resource,category,keys_from(payload),json.dumps(data,ensure_ascii=False),when,captured,snap,
            system+":"+category+":"+copy))

    def records(self,manifest,system,collection,records,location,snapshot,copy="service",closed=True):
        if collection=="operational_record_history":
            for index,row in enumerate(records):self.record_lookup(manifest,row,f"{location}[{index}]",snapshot)
            return
        if collection not in COLLECTIONS:raise InputError("Unknown collection: "+collection)
        _,category=COLLECTIONS[collection]
        members=[]
        for index,row in enumerate(records):
            if not isinstance(row,dict) or not isinstance(row.get("resource_id"),str):raise InputError("Record lacks resource ID")
            data=dict(row)
            members.append(row["resource_id"])
            state=None
            if collection=="profile_lookups":
                if row.get("status_code") not in {200,404}:raise InputError("Unknown profile lookup result")
                data.update(row.get("profile") or {})
                state="ABSENT" if row["status_code"]==404 and row.get("profile") is None else "PRESENT"
            if collection=="index_queries":
                hits=row["hits"]; count=hits["total"]
                if type(count) is not int or count<0 or count!=len(hits["documents"]):raise InputError("Invalid search hit count")
                data.update(hits["documents"][0] if count==1 else {})
                data["_lookup"]=row.get("query")
                state="PRESENT" if count else "ABSENT"
            if collection=="support_conversations":data["_shared_context"]=True
            if collection=="ticket_attachments":data["_subject_only"]=True
            self.add(manifest,system,row["resource_id"],category,data,f"{location}[{index}]",
                     observed=max((timestamp(row[k]) for k in ["observed_at","recorded_at","updated_at"] if row.get(k)),
                                  default=timestamp(snapshot)),snapshot=snapshot,copy=copy,state=state)
        if closed:
            self.add(manifest,system,"",category,dict(members=members,_closed=True),location,snapshot=snapshot,copy=copy,kind="scope",state="SCOPE")

    def record_lookup(self,manifest,row,location,snapshot):
        if row.get("result") not in RESULTS:raise InputError("Unknown readback result")
        self.add(manifest,row["system"],row["resource_id"],row["record_type"],row,location,
                 observed=row.get("recorded_at"),snapshot=snapshot)

    def json(self,manifest,path):
        data=json.loads(path.read_text(encoding="utf-8"))
        snapshot=data.get("exported_at") or data.get("captured_at") or manifest["captured_at"]
        if "snapshots" in data:
            merged=defaultdict(list)
            for index,s in enumerate(data["snapshots"]):
                merged[(s["data_store"],s["collection"],s["captured_at"])].extend(s["records"])
            for (system,collection,time),rows in merged.items():
                self.records(manifest,system,collection,rows,f"snapshots/{system}/{collection}",max((snapshot,time),key=timestamp))
        elif "service_exports" in data:
            for system,collections in data["service_exports"].items():
                for collection,rows in collections.items():self.records(manifest,system,collection,rows,"service_exports/"+system+"/"+collection,snapshot,closed=False)
        elif "records" in data:
            if "record_count" in data and (type(data["record_count"]) is not int or data["record_count"]!=len(data["records"])):
                raise InputError("Declared JSON record count is invalid or inconsistent")
            if all("record_type" in row for row in data["records"]):
                for i,row in enumerate(data["records"]):self.record_lookup(manifest,row,f"records[{i}]",snapshot)
            else:
                collection=data["collection"]
                self.records(manifest,COLLECTIONS[collection][0],collection,data["records"],"records",snapshot)
        else:raise InputError("Unknown JSON dialect")

    def sql(self,manifest,path):
        data=read_snapshot(path.read_text(encoding="utf-8"))
        scopes={r["origin_system"] for r in data.get("snapshot_scope",{}).get("rows",[])}
        for table,contents in data.items():
            if table=="snapshot_scope":continue
            rows=contents["rows"]
            if "record_json" in contents["columns"]:
                copy=table.removeprefix("customer_data_")
                grouped=defaultdict(list)
                for row in rows:
                    record=json.loads(row["record_json"])
                    record["_row_updated_at"]=row["updated_at"]
                    if timestamp(row["updated_at"])>timestamp(manifest["captured_at"]):record["observed_at"]=row["updated_at"]
                    grouped[(row["origin_system"],row["collection_name"])] .append(record)
                for (system,collection),records in grouped.items():
                    self.records(manifest,system,collection,records,"table/"+table+"/"+collection,manifest["captured_at"],copy)
                self.add(manifest,"*","","*",dict(_closed=True,members=[r["resource_id"] for r in rows]),
                         "table/"+table,snapshot=manifest["captured_at"],copy=copy,kind="scope",state="SCOPE")
            else:
                collection=table
                copy="service"
                if table.startswith("customer_profiles_"):
                    collection="customer_profiles";copy=table.removeprefix("customer_profiles_")
                if table=="search_documents_primary":collection="customer_search_documents";copy="primary"
                if collection not in COLLECTIONS:raise InputError("Unknown SQL table: "+table)
                system=COLLECTIONS[collection][0]
                if "snapshot_scope" in data and system not in scopes:
                    if rows:raise InputError("Rows outside SQL declared scope")
                    continue
                self.records(manifest,system,collection,rows,"table/"+table,manifest["captured_at"],copy)

    def text(self,manifest,path):
        text=path.read_text(encoding="utf-8")
        for number,line in enumerate(text.splitlines(),1):
            if not line.startswith("- "):continue
            fields=[x.strip() for x in line[2:].split("|")]
            if len(fields)!=6:raise InputError("Malformed pipe record")
            time,system,resource,category,result,subject=fields
            self.record_lookup(manifest,dict(recorded_at=time,system=system,resource_id=resource,
                record_type=category,result=result,subject_reference=subject),f"line {number}",manifest["captured_at"])

    def log(self,manifest,path):
        parsed=[]
        for number,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
            if not line.strip():continue
            date,rest=line.split(" ",1)
            timestamp(date)
            if rest.startswith("{"):data=json.loads(rest)
            else:
                data={}
                if " message=" in rest:
                    outer=dict(t.split("=",1) for t in shlex.split(rest) if "=" in t)
                    rest=outer["message"]
                    data.update(service=outer.get("function"),trace_id=outer.get("requestId"))
                elif " | " in line:
                    _,_,service,trace,event,rest=line.split(" | ",5)
                    data.update(service=service,trace_id=trace,event=event)
                elif re.match(r"<\d+>1 ",rest):
                    prefix=rest.split(" ",6);data.update(service=prefix[2],trace_id=prefix[3]);rest=prefix[-1]
                elif rest.startswith("["):
                    m=re.match(r"\[[^]]+\] \[([^]]+)\] \[([^]]+)\] (\w+): (.*)",rest)
                    if not m:raise InputError("Unknown bracket log")
                    data.update(service=m[1],trace_id=m[2],event=m[3]);rest=m[4]
                for token in shlex.split(rest):
                    if "=" in token:
                        key,value=token.split("=",1);data[key]=value
            for k,v in list(data.items()):
                if v=="true":data[k]=True
                elif v=="false":data[k]=False
                elif v=="null":data[k]=None
                elif isinstance(v,str) and re.fullmatch(r"\d+",v):data[k]=int(v)
            parsed.append((timestamp(date),number,date,data))
        traces={}
        recognized=0
        for _,number,date,data in sorted(parsed):
            service=data.get("service");trace=(service,data.get("trace_id"))
            event=data.get("event","")
            history=traces.setdefault(trace,[]) if trace[1] else []
            if trace[1] and event.endswith("_started"):
                history=[];traces[trace]=history
            history.append((number,data))
            resource=data.get("resource_id")
            if not resource:continue
            payload={}
            for _,part in history:payload.update(part)
            payload.update(data)
            location="lines "+",".join(str(n) for n,_ in history) if trace[1] else f"line {number}"
            if event=="record_lookup":
                self.record_lookup(manifest,payload,location,manifest["captured_at"]);recognized+=1;continue
            category=None;state=None
            if event=="profile_lookup_completed":category="USER_PROFILE"
            elif event=="index_query_completed":category="SEARCH_INDEX_ENTRY"
            elif event in {"contact_query_completed","contact_lookup_completed"}:category="SECONDARY_IDENTIFIER"
            elif event.startswith("analytics_") and event in {"analytics_profile_read_completed","analytics_profile_read","analytics_identity_scan"}:
                category="ANALYTICS_PROFILE"
                if data.get("direct_identifiers")==0:state="ANONYMIZED"
                elif data.get("matched_value"):state="IDENTIFIABLE"
            elif event in {"message_pii_scan","support_ticket_read_completed"}:category="SUPPORT_MESSAGE"
            elif event=="attachment_pii_scan":category="SUPPORT_ATTACHMENT"
            elif event=="audit_record_read_completed":category="SECURITY_AUDIT_LOG"
            elif event in {"connector_heartbeat","connector_config_read_completed","connector_config_loaded"}:category="DATA_FLOW"
            elif event in {"restore_policy_read_completed","restore_candidate_evaluated","restore_policy_loaded"}:
                category="BACKUP_ARCHIVE"
                if "deletion_block" in payload:payload["restore_allowed"]=not payload["deletion_block"]
            elif event in {"export_download_check_completed","export_metadata_read_completed"}:category="USER_EXPORT"
            if not category:continue
            if event in {"message_pii_scan","attachment_pii_scan","analytics_identity_scan"}:state="IDENTIFIABLE"
            if category=="SUPPORT_ATTACHMENT":payload["_subject_only"]=True
            if category=="SUPPORT_MESSAGE":payload["_shared_context"]=True
            self.add(manifest,service,resource,category,payload,location,observed=date,state=state)
            recognized+=1
        if not recognized:raise InputError("No supported log observations")

    def business(self,manifest,path):
        if self.jobs is None:raise InputError("Business interpretation requires runtime AI")
        if path.suffix==".pdf":
            source=subprocess.check_output(["pdftotext","-layout",str(path),"-"],text=True,timeout=30)
            attachment=None
        else:
            source=subprocess.check_output(["tesseract",str(path),"stdout"],text=True,stderr=subprocess.DEVNULL,timeout=30)
            source+="\nSECOND OCR PASS\n"+subprocess.check_output(["tesseract",str(path),"stdout","--psm","6"],text=True,stderr=subprocess.DEVNULL,timeout=30)
            attachment=path
        pages=source.split("\f")
        prompt=Path(__file__).with_name("runtime").joinpath("evidence.md").read_text(encoding="utf-8")
        categories=[r["data_category"] for r in self.tables["deletion_rules.csv"]]+["DATA_FLOW"]
        prompt+="\nPolicy category vocabulary: "+json.dumps(categories)+"\n<untrusted-pages>\n"
        prompt+="\n".join(f"PAGE {i+1}\n{p}" for i,p in enumerate(pages))+"\n</untrusted-pages>"
        def validate(response):
            if not isinstance(response,dict) or set(response)!={"records","uncertainties"}:raise RuntimeFailure("Invalid evidence schema")
            if not isinstance(response["records"],list) or not isinstance(response["uncertainties"],list):raise RuntimeFailure("Invalid evidence arrays")
            if not response["records"]:raise RuntimeFailure("Empty business interpretation is not proof of absence")
            for row in response["records"]:
                if set(row)!={"system_id","resource_id","business_key","category","fields","quote","page"}:raise RuntimeFailure("Invalid business record fields")
                if type(row["page"]) is not int or not 1<=row["page"]<=len(pages):raise RuntimeFailure("Invalid page number")
                if row["category"] not in categories or not isinstance(row["fields"],dict):raise RuntimeFailure("Invalid category or field payload")
                services={s for s,_ in COLLECTIONS.values()}|{"object_storage","support_replica"}
                if row["system_id"] not in services:raise RuntimeFailure("Use a supplied canonical service ID, not a product/company name")
                if any(k.startswith("_") for k in row["fields"]):raise RuntimeFailure("Reserved parser metadata in model fields")
                if row["resource_id"] in {u["user_id"] for u in self.tables["user_identities.csv"]}:
                    raise RuntimeFailure("Stable user reference is not a canonical resource ID; use a displayed record ID or business_key")
                quote=row["quote"]
                if not isinstance(quote,str) or not quote.strip() or " ".join(quote.split()) not in " ".join(pages[row["page"]-1].split()):raise RuntimeFailure("Business quote not corroborated by extracted page text")
                for key in ["resource_id","business_key"]:
                    value=row[key]
                    if value is not None and (not isinstance(value,str) or not value):raise RuntimeFailure("Invalid business identifier")
                    if value is not None and value not in pages[row["page"]-1] and attachment is None:
                        raise RuntimeFailure("Uncorroborated document identifier")
            return response
        response=self.jobs.request(prompt,"preprocessing",dict(artifact_ids=[manifest["file_id"]]),validate,attachment)
        records=list(response["records"])
        if path.suffix==".pdf" and "Attachment properties and upload history" in source:
            documents=[r for r in records if r["category"]=="SUPPORT_MESSAGE" and r["resource_id"]]
            uploads=[r for r in records if r["category"]=="SUPPORT_ATTACHMENT" and r["resource_id"] is None]
            if len(documents)==len(uploads)==1:
                document,upload=documents[0],uploads[0]
                if (document["system_id"]==upload["system_id"]=="support_platform"
                        and document["business_key"] and document["business_key"]==upload["fields"].get("ticket")):
                    # The upload metadata describes this document, not a separate conversation record.
                    combined=dict(upload,resource_id=document["resource_id"],fields=dict(document["fields"],**upload["fields"]))
                    combined["fields"]["_container_identifier_source"]=dict(page=document["page"],quote=document["quote"])
                    records=[r for r in records if r is not document and r is not upload]+[combined]
        for i,row in enumerate(records):
            fields=dict(row["fields"],_business_key=row["business_key"],_quote=row["quote"])
            corroboration={}
            if attachment:
                page=pages[row["page"]-1]
                for key in ["resource_id","business_key"]:
                    if row[key] and row[key] not in page:corroboration[key]=row[key]
                for key,field in KEY_FIELDS.items():
                    value=row["fields"].get(key)
                    if isinstance(value,str) and value and " ".join(value.split()) not in " ".join(page.split()):
                        corroboration[field]=value
            fields["_corroboration_required"]=corroboration
            fields["_extraction_uncertainties"]=response["uncertainties"]
            if row["category"]=="SUPPORT_ATTACHMENT":fields["_subject_only"]=True
            location=f'page {row["page"]} record {i}'
            if fields.get("_container_identifier_source"):
                location+=f'; identifier on page {fields["_container_identifier_source"]["page"]}'
            self.add(manifest,row["system_id"],row["resource_id"] or "",row["category"],fields,location)

    def run(self,structured_only=False):
        for row in self.tables["evidence_files.csv"]:
            path=evidence_path(self.dataset,row["file_path"])
            entry=dict(run_id=RUN_ID,file_id=row["file_id"],
                       path=row["file_path"],captured_at=row["captured_at"],sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            before=len(self.facts)
            try:
                handler={".json":self.json,".sql":self.sql,".txt":self.text,".log":self.log}.get(path.suffix)
                if handler:handler(row,path)
                elif structured_only:entry["skipped"]=True
                else:self.business(row,path)
            except (ValueError,KeyError,TypeError,OSError,subprocess.SubprocessError,RuntimeFailure) as exc:
                entry["error"]=str(exc)
                # Partial parser success cannot be consumed as a closed successful scan.
                del self.facts[before:]
            entry["facts"]=len(self.facts)-before
            self.ledger.append(entry)
        return self.facts,self.ledger
