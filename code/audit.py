"""As-of resource reconstruction and deletion-policy PLANNING, never live actions."""

from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone
import json
import re

from extract import EMAIL, keys_from
from facts import Fact, normalize, resolve_identity
from inputs import InputError, timestamp
from steps import canonical_steps, validate_steps


def retention_deadline(value):
    """Business-document dates are source facts, not CSV timestamp syntax."""
    try:
        return timestamp(value)
    except InputError:
        for fmt in ["%d %b %Y %H %M UTC", "%d %b %Y %H:%M UTC", "%d %b %Y", "%Y-%m-%d"]:
            try:
                parsed=datetime.strptime(value,fmt).replace(tzinfo=timezone.utc)
            except (ValueError,TypeError):
                continue
            # A date without a time cannot prove retention past that day's start.
            return parsed
        raise InputError("Unrecognized supplied retention deadline")


def activity_facts(rows):
    facts=[]
    for number,row in enumerate(rows,2):
        time=timestamp(row["event_time"])
        payload=dict(row)
        kind="activity_claim"
        if row["event_type"]=="LINK_RESOURCE_IDENTITY":
            kind="identity_link"
            match=re.search(r"\(([^)]+)\)",row["details"])
            if match:payload["business_key"]=match[1]
        keys=set(keys_from(payload))
        keys.update(("user_id",u) for u in re.findall(r"\buser_[A-Za-z0-9_-]+\b",row["details"]))
        keys.update(("email",email.casefold()) for email in re.findall(EMAIL,row["details"]))
        facts.append(Fact(row["activity_id"],row["activity_id"],"system_activity.csv",f"row {row.get('_source_row',number)}",kind,
            row["target_system"],row["resource_id"],"",tuple(sorted(keys)),json.dumps(payload),time,time,time,"activity"))
    return facts


def policy_action(category,payload,cutoff,rules):
    if category=="DATA_FLOW":return "DISABLE"
    rule=rules.get(category)
    if rule is None:raise InputError("Unknown policy category: "+category)
    condition=rule["condition"]
    if condition=="Always":return rule["required_action"]
    if category=="SUPPORT_MESSAGE":
        if not payload.get("_shared_context") and not payload.get("message_excerpt"):
            raise InputError("Shared support-context condition not established")
    elif category=="SUPPORT_ATTACHMENT":
        if not payload.get("_subject_only"):raise InputError("Exclusive attachment ownership not established")
    elif category in {"ANALYTICS_PROFILE","PRODUCT_TELEMETRY"}:
        if payload.get("_state") not in {"IDENTIFIABLE","ANONYMIZED"}:raise InputError("Analytics attribution unknown")
    elif category=="EMAIL_DELIVERY_LOG":
        if "email" not in payload and payload.get("_state")!="REDACTED":raise InputError("Delivery-log identifier condition unknown")
    elif category in {"SECURITY_AUDIT_LOG","LEGAL_HOLD_RECORD"}:
        end=payload.get("retention_until") or payload.get("retained_until")
        active=payload.get("legal_hold_active") if category=="LEGAL_HOLD_RECORD" else payload.get("_retention_confirmed")
        if not (active is True or isinstance(end,str) and retention_deadline(end)>cutoff):
            raise InputError("Supplied retention/hold period is not established as active")
    elif category=="BACKUP_ARCHIVE":
        if payload.get("_state") not in {"ACTIVE","BLOCKED"}:raise InputError("Restore controls are not established")
    elif category=="ACCOUNT_TOMBSTONE":
        if payload.get("account_status")!="DELETED" or not any(payload.get(k) for k in ["subject_reference","user_id","customer_reference"]):
            raise InputError("Required tombstone stable reference/deleted-account condition missing")
    else:raise InputError("Unsupported policy condition: "+condition)
    return rule["required_action"]


class AuditEngine:
    def __init__(self,tables,facts,coverage=()):
        self.tables=tables
        self.facts=list(facts)+activity_facts(tables.get("system_activity.csv",[]))
        self.coverage=list(coverage)
        self.rules={r["data_category"]:r for r in tables["deletion_rules.csv"]}

    def supports(self,request,decision,step):
        """Recheck serialized citations against source facts, not the generated text."""
        cutoff=timestamp(request["audit_at"])
        key="|".join(step[k] for k in ["phase","operation","system_id","resource_id"])
        ids=set(decision.get("proof",{}).get(key,[]))
        category=next((r["category"] for r in decision.get("resources",[])
                       if (r["system_id"],r["resource_id"])==(step["system_id"],step["resource_id"])),None)
        if category is None:return False
        expected={"REPORT_REMAINING_RECORD":{"PRESENT","IDENTIFIABLE","REDACTED","ANONYMIZED"},
            "REPORT_EXPOSED_PII":{"IDENTIFIABLE"},"REPORT_ACTIVE_DATA_FLOW":{"ACTIVE"},"REPORT_RESTORE_RISK":{"ACTIVE"},
            "VERIFY_RECORD_ABSENT":{"ABSENT"},"VERIFY_RECORD_PRESENT":{"PRESENT","IDENTIFIABLE","REDACTED","ANONYMIZED"},
            "VERIFY_RECORD_REDACTED":{"REDACTED"},"VERIFY_RECORD_ANONYMIZED":{"ANONYMIZED"},
            "VERIFY_DATA_FLOW_DISABLED":{"DISABLED"},"VERIFY_RESTORE_BLOCKED":{"BLOCKED"}}.get(step["operation"],set())
        for fact in self.facts:
            if fact.fact_id not in ids or fact.evidence_id!=step["evidence_id"] or not fact.eligible(cutoff):continue
            if fact.system_id not in {step["system_id"],"*"}:continue
            data=json.loads(fact.payload_json)
            if fact.claim_kind=="scope":
                if (expected=={"ABSENT"} and data.get("_closed") and fact.category in {category,"*"}
                        and isinstance(data.get("members"),list) and step["resource_id"] not in data["members"]):
                    return True
            elif fact.claim_kind=="observation" and data.get("_state") in expected:
                if fact.resource_id==step["resource_id"]:return True
                if not fact.resource_id:
                    business={v for k,v in fact.subject_keys if k=="business_key"}
                    if any(link.claim_kind=="identity_link" and link.eligible(cutoff)
                           and link.system_id==step["system_id"] and link.resource_id==step["resource_id"]
                           and business.intersection(v for k,v in link.subject_keys if k=="business_key")
                           for link in self.facts):return True
        return False

    def decide(self,request,authorized):
        result=dict(case_id=request["case_id"],authorized=authorized,diagnostics=[],resources=[],steps=[],status=None,proof={})
        if authorized is False:
            result.update(status="NOT_APPLICABLE")
            return result
        if authorized is not True:
            result["diagnostics"].append("Unresolved authorization: "+str(authorized));return result
        cutoff=timestamp(request["audit_at"])
        requested=timestamp(request["requested_at"])
        try:
            user,aliases=resolve_identity(request["email"],cutoff,self.tables["user_identities.csv"],self.tables["user_audit_log.csv"])
        except InputError as exc:
            result["diagnostics"].append(str(exc));return result
        own={(a.field,a.normalized) for a in aliases if a.field!="name"}
        owners=defaultdict(set)
        for row in self.tables["user_identities.csv"]:
            if timestamp(row["updated_at"])<=cutoff:
                owners[("user_id",row["user_id"])].add(row["user_id"])
                for field in ["email","phone","email_hash"]:
                    if row[field]:owners[(field,normalize(field,row[field]))].add(row["user_id"])
        for row in self.tables["user_audit_log.csv"]:
            if timestamp(row["event_time"])<=cutoff:
                owners[("user_id",row["user_id"])].add(row["user_id"])
                if row["field_name"] in {"email","phone","email_hash"}:
                    for field in ["old_value","new_value"]:
                        if row[field]:owners[(row["field_name"],normalize(row["field_name"],row[field]))].add(row["user_id"])
        eligible=[f for f in self.facts if f.eligible(cutoff)]
        payloads={f.fact_id:json.loads(f.payload_json) for f in eligible}
        known=set()
        linked=set()
        ambiguous=[]
        for fact in eligible:
            if own.intersection(fact.subject_keys):
                matched=own.intersection(fact.subject_keys)
                if not any(owners.get(key)=={user} for key in matched):
                    ambiguous.append(fact)
                    continue
                foreign={v for k,v in fact.subject_keys if k=="user_id" and v!=user}
                if foreign:
                    result["diagnostics"].append("Conflicting subject reference: "+fact.fact_id);continue
                linked.add(fact.fact_id)
                if fact.resource_id:known.add((fact.system_id,fact.resource_id))
        # Fixed-point closure over explicit resource pointers and eligible business catalog links.
        bound=[]
        changed=True
        while changed:
            changed=False
            resource_ids={r for _,r in known}
            for fact in eligible:
                if fact.claim_kind=="scope":continue
                data=payloads[fact.fact_id]
                key=(fact.system_id,fact.resource_id)
                belongs=key in known and bool(fact.resource_id)
                if not belongs and any(k=="resource" and v in resource_ids for k,v in fact.subject_keys):belongs=True
                if belongs and key not in known:
                    known.add(key);changed=True
                if belongs:
                    linked.add(fact.fact_id)
                    for k,v in fact.subject_keys:
                        if k=="resource":
                            for candidate in eligible:
                                if candidate.resource_id==v and (candidate.system_id,v) not in known:
                                    known.add((candidate.system_id,v));changed=True
            for fact in eligible:
                if fact.resource_id or fact.claim_kind!="observation":continue
                business={v for k,v in fact.subject_keys if k=="business_key"}
                if not business:continue
                matches=[link for link in eligible if link.claim_kind=="identity_link"
                    and link.fact_id in linked and link.system_id==fact.system_id
                    and business.intersection(v for k,v in link.subject_keys if k=="business_key")]
                resources={m.resource_id for m in matches}
                if len(resources)==1:
                    resource=next(iter(resources))
                    bound_fact=replace(fact,resource_id=resource)
                    if not any(f.fact_id==fact.fact_id for f in bound):bound.append(bound_fact)
        observations=[]
        for fact in ambiguous:
            if (fact.system_id,fact.resource_id) not in known and not any(f.fact_id==fact.fact_id for f in bound):
                result["diagnostics"].append("Shared identifier requires independent ownership corroboration: "+fact.fact_id)
        for fact in eligible:
            if fact.claim_kind!="observation" or (fact.system_id,fact.resource_id) not in known:continue
            foreign={v for k,v in fact.subject_keys if k=="user_id" and v!=user}
            if foreign:
                result["diagnostics"].append("Resource has conflicting subject ownership: "+fact.fact_id)
            else:observations.append(fact)
        observations+=bound
        for fact in observations:
            data=payloads[fact.fact_id]
            if data.get("_extraction_uncertainties"):
                result["diagnostics"].append("Owned evidence has extraction uncertainties: "+fact.fact_id)
            for kind,value in data.get("_corroboration_required",{}).items():
                if kind in {"resource_id","business_key"}:
                    supported=any(other.path!=fact.path and other.fact_id in linked and
                        (other.resource_id==value if kind=="resource_id" else ("business_key",value) in other.subject_keys)
                        for other in eligible)
                else:supported=(kind,normalize(kind,value)) in own
                if not supported:result["diagnostics"].append("Uncorroborated visual key: "+fact.fact_id+":"+kind)
        for fact in eligible:
            if (fact.claim_kind=="observation" and not fact.resource_id
                    and own.intersection(fact.subject_keys)
                    and not any(f.fact_id==fact.fact_id for f in bound)):
                result["diagnostics"].append("Owned business record has no grounded canonical resource: "+fact.fact_id)
        for fact in bound:known.add((fact.system_id,fact.resource_id))
        scopes=[f for f in eligible if f.claim_kind=="scope"]
        # An eligible parse failure has unknown membership: conservatively fail affected authorization,
        # rather than claim that absence of parsed rows is a complete global search.
        for entry in self.coverage:
            if entry.get("error") and timestamp(entry["captured_at"])<=cutoff:
                result["diagnostics"].append("Unresolved extraction: "+entry["file_id"]+": "+entry["error"])
        groups=defaultdict(list)
        for fact in observations:groups[(fact.system_id,fact.resource_id)].append(fact)
        findings=[];repairs=[];checks=[];proof={}
        for key in sorted(known):
            system,resource=key
            actual=groups.get(key,[])
            categories={f.category for f in actual}
            if len(categories)!=1:
                result["diagnostics"].append(f"Unresolved resource category/state: {system}/{resource}");continue
            category=next(iter(categories))
            candidates=list(actual)
            copies={json.loads(f.payload_json)["_copy"] for f in actual}
            for scope in scopes:
                s=json.loads(scope.payload_json)
                if (scope.system_id in {system,"*"} and scope.category in {category,"*"}
                        and s.get("_closed") and resource not in s["members"]
                        and s["_copy"] in copies):
                    candidates.append(replace(scope,resource_id=resource,system_id=system,category=category,
                        claim_kind="observation",payload_json=json.dumps(dict(_state="ABSENT",_copy=s["_copy"],_derived_scope=scope.fact_id))))
            reduced=[]
            for copy in sorted(copies):
                same=[f for f in candidates if json.loads(f.payload_json)["_copy"]==copy]
                latest=max(f.observed_at for f in same)
                newest=[f for f in same if f.observed_at==latest]
                states={json.loads(f.payload_json)["_state"] for f in newest}
                if len(states)!=1:
                    result["diagnostics"].append(f"Conflicting same-copy observations: {system}/{resource}/{copy}");continue
                reduced.append(sorted(newest,key=lambda f:(f.evidence_id,f.location))[0])
            if not reduced:continue
            # Preserve a historical obligation when no source establishes its state in this request.
            # This is an uncertainty diagnostic, never a TTL, implicit deletion or ignored record.
            if max(f.observed_at for f in reduced)<requested:
                result["diagnostics"].append(f"Historical obligation lacks as-of continuity: {system}/{resource}")
            merged={}
            for f in sorted(actual,key=lambda f:f.observed_at):merged.update(json.loads(f.payload_json))
            states={json.loads(f.payload_json)["_state"] for f in reduced}
            if "UNKNOWN" in states:
                result["diagnostics"].append(f"Unknown observed treatment: {system}/{resource}");continue
            if category=="ACCOUNT_TOMBSTONE" and not any(f.category=="USER_PROFILE" and json.loads(f.payload_json)["_state"]=="ABSENT" for f in observations):
                result["diagnostics"].append(f"Tombstone lacks grounded deleted-account readback: {resource}")
            try:action=policy_action(category,merged,cutoff,self.rules)
            except InputError as exc:
                result["diagnostics"].append(f"{system}/{resource}: {exc}");continue
            expected={"DELETE":"ABSENT","REDACT":"REDACTED","ANONYMIZE":"ANONYMIZED",
                      "RETAIN":"PRESENT","DISABLE":"DISABLED"}[action]
            if category=="BACKUP_ARCHIVE":expected="BLOCKED"
            violations=[f for f in reduced if json.loads(f.payload_json)["_state"]!=expected]
            if action=="RETAIN" and category!="BACKUP_ARCHIVE":
                violations=[f for f in reduced if json.loads(f.payload_json)["_state"]=="ABSENT"]
            if violations and (action=="RETAIN" and category!="BACKUP_ARCHIVE" or "ABSENT" in states and action in {"REDACT","ANONYMIZE"}):
                result["diagnostics"].append(f"Required retained record missing; no safe allowed repair: {system}/{resource}");continue
            verify={"ABSENT":"VERIFY_RECORD_ABSENT","PRESENT":"VERIFY_RECORD_PRESENT","REDACTED":"VERIFY_RECORD_REDACTED",
                    "ANONYMIZED":"VERIFY_RECORD_ANONYMIZED","DISABLED":"VERIFY_DATA_FLOW_DISABLED","BLOCKED":"VERIFY_RESTORE_BLOCKED"}[expected]
            selected=sorted(violations or reduced,key=lambda f:(-f.observed_at.timestamp(),f.evidence_id,f.location))[0]
            def make(phase,operation,state,evidence):
                return dict(step_no=0,phase=phase,system_id=system,resource_id=resource,operation=operation,state=state,evidence_id=evidence)
            checks.append(make("VERIFICATION",verify,expected,selected.evidence_id))
            proof[("VERIFICATION",verify,system,resource)]=[f for f in reduced]
            if violations:
                if category=="DATA_FLOW":finding,repair,state="REPORT_ACTIVE_DATA_FLOW","DISABLE_DATA_FLOW","ACTIVE"
                elif category=="BACKUP_ARCHIVE":finding,repair,state="REPORT_RESTORE_RISK","BLOCK_RESTORE","ACTIVE"
                elif action=="DELETE":finding,repair,state="REPORT_REMAINING_RECORD","DELETE_RECORD","PRESENT"
                else:finding,repair,state="REPORT_EXPOSED_PII",action+"_RECORD","PRESENT"
                findings.append(make("FINDING",finding,state,selected.evidence_id))
                repairs.append(make("REMEDIATION",repair,expected,""))
                proof[("FINDING",finding,system,resource)]=violations
            result["resources"].append(dict(system_id=system,resource_id=resource,category=category,
                expected=expected,states=sorted(states),fact_ids=[f.fact_id for f in reduced],
                locations=[dict(evidence_id=f.evidence_id,path=f.path,location=f.location) for f in reduced]))
        if not any(r["category"]=="USER_PROFILE" for r in result["resources"]):
            result["diagnostics"].append("No grounded account resource/state proof")
        if not checks:result["diagnostics"].append("No complete required final-state checks")
        if result["diagnostics"]:return result
        status="INCOMPLETE" if findings else "COMPLETE"
        if findings:
            for s in checks:s["evidence_id"]=""
        steps=canonical_steps(findings+repairs+checks)
        def supports(step):
            items=proof.get((step["phase"],step["operation"],step["system_id"],step["resource_id"]),[])
            return any(f.evidence_id==step["evidence_id"] and f.eligible(cutoff) for f in items)
        validate_steps(status,steps,supports)
        result.update(status=status,steps=steps,proof={"|".join(k):[f.fact_id for f in v] for k,v in proof.items()})
        return result
