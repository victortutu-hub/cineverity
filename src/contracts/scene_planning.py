"""Scene Planning Contract v0.1: strict Director + Physical Constraints planning boundary."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Literal, Optional

from pydantic import Field, StrictBool, model_validator

from src.contracts.director_intent import Priority, StrictModel
from src.contracts.physical_constraints import (
    ArtisticDeviationType, MaterialIdentityStatus, PhysicalAssessmentStatus,
    PhysicalConflictResolutionStatus,
)
from src.contracts.research_evidence import MaterialUnknownParameterReference


class SceneDecisionStatus(str, Enum): committed='committed'; conditional='conditional'; deferred='deferred'
class SceneDecisionKind(str, Enum):
    physically_grounded_realization='physically_grounded_realization'; implementation_choice='implementation_choice'; artistic_deviation_realization='artistic_deviation_realization'; unresolved_dependency_handling='unresolved_dependency_handling'
class SceneParameterCategory(str, Enum): geometry='geometry'; material='material'; lighting='lighting'; camera='camera'; environment='environment'; temporal='temporal'
class SceneParameterRole(str, Enum): implementation_choice='implementation_choice'; artistic_realization='artistic_realization'; provisional_placeholder='provisional_placeholder'; unresolved='unresolved'
class SceneParameterValueKind(str, Enum): numeric='numeric'; categorical='categorical'; descriptive='descriptive'; boolean='boolean'; unresolved='unresolved'
class SceneMaterialIdentityMode(str, Enum): established='established'; unresolved_abstract='unresolved_abstract'; provisional_placeholder='provisional_placeholder'
class ScenePlanningDependencyKind(str, Enum): unresolved_physical_constraint='unresolved_physical_constraint'; physical_conflict='physical_conflict'; material_identity_uncertainty='material_identity_uncertainty'; artist_acceptance='artist_acceptance'; artist_decision='artist_decision'
class SceneCoverageSubjectKind(str, Enum): physical_constraint='physical_constraint'; physical_conflict='physical_conflict'; unresolved_physical_constraint='unresolved_physical_constraint'; artistic_deviation='artistic_deviation'
class SceneCoverageState(str, Enum): realized='realized'; constrains_decision='constrains_decision'; conditional='conditional'; deferred='deferred'
class SceneValidationHookKind(str, Enum): director_target_check='director_target_check'; physical_constraint_check='physical_constraint_check'; artistic_deviation_disclosure_check='artistic_deviation_disclosure_check'; unresolved_dependency_check='unresolved_dependency_check'; physical_conflict_check='physical_conflict_check'

class PhysicalConstraintScopeReference(StrictModel):
    physical_constraint_id: str = Field(..., min_length=1); status: PhysicalAssessmentStatus; director_scene_entity_ids:list[str]; director_physical_question_ids:list[str]; related_material_unknown_parameters:list[MaterialUnknownParameterReference]
class PhysicalConflictScopeReference(StrictModel):
    physical_conflict_id:str=Field(..., min_length=1); resolution_status:PhysicalConflictResolutionStatus; physical_constraint_ids:list[str]; director_physical_question_ids:list[str]
class UnresolvedPhysicalConstraintScopeReference(StrictModel):
    unresolved_physical_constraint_id:str=Field(..., min_length=1); director_scene_entity_ids:list[str]; director_physical_question_ids:list[str]; related_material_unknown_parameters:list[MaterialUnknownParameterReference]
class ArtisticDeviationScopeReference(StrictModel):
    artistic_deviation_id:str=Field(..., min_length=1); deviation_type:ArtisticDeviationType; requires_explicit_artist_acceptance:StrictBool; director_scene_entity_ids:list[str]; director_physical_question_ids:list[str]; related_material_unknown_parameters:list[MaterialUnknownParameterReference]
class SceneMaterialIdentityScopeReference(StrictModel):
    physical_constraint_id:str=Field(..., min_length=1); scene_entity_id:str=Field(..., min_length=1); status:MaterialIdentityStatus; identity_label:Optional[str]=None
class SceneMaterialIdentitySelector(StrictModel):
    physical_constraint_id:str=Field(..., min_length=1); scene_entity_id:str=Field(..., min_length=1)
class ScenePlanningScope(StrictModel):
    director_contract_sha256:str=Field(..., pattern=r'^[0-9a-f]{64}$'); physical_constraints_contract_sha256:str=Field(..., pattern=r'^[0-9a-f]{64}$')
    director_scene_entity_ids:list[str]; director_validation_target_ids:list[str]; director_physical_question_ids:list[str]; director_material_unknown_parameters:list[MaterialUnknownParameterReference]
    physical_constraint_references:list[PhysicalConstraintScopeReference]; physical_conflict_references:list[PhysicalConflictScopeReference]; unresolved_physical_constraint_references:list[UnresolvedPhysicalConstraintScopeReference]; artistic_deviation_references:list[ArtisticDeviationScopeReference]; material_identity_references:list[SceneMaterialIdentityScopeReference]
class SceneDecisionBasis(StrictModel):
    director_physical_question_ids:list[str]; grounding_constraint_ids:list[str]; constraining_constraint_ids:list[str]; physical_conflict_ids:list[str]; artistic_deviation_ids:list[str]; unresolved_physical_constraint_ids:list[str]; implementation_rationale:Optional[str]=None
class ScenePlanDecision(StrictModel):
    id:str=Field(...,min_length=1); kind:SceneDecisionKind; status:SceneDecisionStatus; description:str=Field(...,min_length=1); target_scene_entity_ids:list[str]; basis:SceneDecisionBasis; conditions:list[str]; dependency_ids:list[str]
class SceneParameterValue(StrictModel):
    kind:SceneParameterValueKind; numeric_value:Optional[str]=None; categorical_value:Optional[str]=None; descriptive_value:Optional[str]=None; boolean_value:Optional[StrictBool]=None; unit:Optional[str]=None
    @model_validator(mode='after')
    def exclusive(self):
        values=[self.numeric_value is not None,self.categorical_value is not None,self.descriptive_value is not None,self.boolean_value is not None]
        if self.kind is SceneParameterValueKind.numeric:
            if values != [True,False,False,False]: raise ValueError('numeric SceneParameterValue requires only numeric_value')
            try:
                if not Decimal(self.numeric_value).is_finite(): raise ValueError
            except (InvalidOperation,ValueError): raise ValueError('numeric SceneParameterValue must be finite Decimal')
        elif self.kind is SceneParameterValueKind.categorical:
            if values != [False,True,False,False] or not self.categorical_value: raise ValueError('categorical SceneParameterValue requires only categorical_value')
        elif self.kind is SceneParameterValueKind.descriptive:
            if values != [False,False,True,False] or not self.descriptive_value: raise ValueError('descriptive SceneParameterValue requires only descriptive_value')
        elif self.kind is SceneParameterValueKind.boolean:
            if values != [False,False,False,True]: raise ValueError('boolean SceneParameterValue requires only boolean_value')
        elif any(values) or self.unit is not None: raise ValueError('unresolved SceneParameterValue cannot contain concrete values or unit')
        return self
class SceneParameterAssignment(StrictModel):
    id:str=Field(...,min_length=1); decision_id:str=Field(...,min_length=1); target_scene_entity_id:Optional[str]=None; parameter_name:str=Field(...,min_length=1); category:SceneParameterCategory; role:SceneParameterRole; value:SceneParameterValue; dependency_ids:list[str]
class SceneMaterialPlan(StrictModel):
    id:str=Field(...,min_length=1); decision_id:str=Field(...,min_length=1); scene_entity_id:str=Field(...,min_length=1); identity_mode:SceneMaterialIdentityMode; material_identity_selector:Optional[SceneMaterialIdentitySelector]=None; identity_label:Optional[str]=None; limitation:Optional[str]=None; dependency_ids:list[str]
class ScenePlanningDependency(StrictModel):
    id:str=Field(...,min_length=1); kind:ScenePlanningDependencyKind; unresolved_physical_constraint_id:Optional[str]=None; physical_conflict_id:Optional[str]=None; material_identity_selector:Optional[SceneMaterialIdentitySelector]=None; artistic_deviation_id:Optional[str]=None; reason:str=Field(...,min_length=1)
class ArtisticDeviationRealization(StrictModel):
    id:str=Field(...,min_length=1); artistic_deviation_id:str=Field(...,min_length=1); deviation_type:ArtisticDeviationType; requires_explicit_artist_acceptance:StrictBool; target_scene_entity_ids:list[str]; decision_ids:list[str]; status:SceneDecisionStatus; dependency_ids:list[str]; description:str=Field(...,min_length=1)
class TemporalBeat(StrictModel): id:str=Field(...,min_length=1); sequence_index:int=Field(...,ge=0); description:str=Field(...,min_length=1); decision_ids:list[str]
class SceneShotPlan(StrictModel): id:str=Field(...,min_length=1); sequence_index:int=Field(...,ge=0); purpose:str=Field(...,min_length=1); decision_ids:list[str]; temporal_beats:list[TemporalBeat]
class SceneValidationHook(StrictModel):
    id:str=Field(...,min_length=1); kind:SceneValidationHookKind; description:str=Field(...,min_length=1); decision_ids:list[str]; dependency_ids:list[str]; director_validation_target_ids:list[str]; physical_constraint_ids:list[str]; artistic_deviation_ids:list[str]; unresolved_physical_constraint_ids:list[str]; physical_conflict_ids:list[str]
class ScenePlanningCoverage(StrictModel): subject_kind:SceneCoverageSubjectKind; subject_id:str=Field(...,min_length=1); state:SceneCoverageState; decision_ids:list[str]; dependency_ids:list[str]; validation_hook_ids:list[str]; reason:Optional[str]=None

class ScenePlanningContract(StrictModel):
    contract_version:Literal['0.1']; agent:Literal['scene_planning_agent']; input_scope:ScenePlanningScope; decisions:list[ScenePlanDecision]; parameter_assignments:list[SceneParameterAssignment]; material_plans:list[SceneMaterialPlan]; dependencies:list[ScenePlanningDependency]; artistic_deviation_realizations:list[ArtisticDeviationRealization]; shot_plan:list[SceneShotPlan]; validation_hooks:list[SceneValidationHook]; coverage:list[ScenePlanningCoverage]; scene_plan_summary:str=Field(...,min_length=1)
    @model_validator(mode='after')
    def validate_contract(self):
        def ids(items,attr,label):
            values=[getattr(x,attr) for x in items]
            if any(not x for x in values) or len(values)!=len(set(values)): raise ValueError(f'Duplicate or blank {label}')
            return set(values)
        def refs(values,allowed,label):
            if any(not x for x in values) or len(values)!=len(set(values)) or not set(values)<=allowed: raise ValueError(f'Invalid {label}')
        s=self.input_scope
        def membership(values, label):
            if any(not value for value in values) or len(values) != len(set(values)):
                raise ValueError(f'Duplicate or blank {label}')
        membership(s.director_scene_entity_ids, 'scope scene entity IDs')
        membership(s.director_validation_target_ids, 'scope validation target IDs')
        membership(s.director_physical_question_ids, 'scope physical question IDs')
        unknown_scope_pairs=[(item.entity_id, item.parameter) for item in s.director_material_unknown_parameters]
        if any(not entity_id or not parameter for entity_id, parameter in unknown_scope_pairs) or len(unknown_scope_pairs) != len(set(unknown_scope_pairs)):
            raise ValueError('Duplicate or blank scope material unknown pairs')
        if any(entity_id not in s.director_scene_entity_ids for entity_id, _ in unknown_scope_pairs): raise ValueError('Scope material unknown references unknown entity')
        for references, attr, label in ((s.physical_constraint_references, 'physical_constraint_id', 'scope physical constraint references'), (s.physical_conflict_references, 'physical_conflict_id', 'scope physical conflict references'), (s.unresolved_physical_constraint_references, 'unresolved_physical_constraint_id', 'scope unresolved references'), (s.artistic_deviation_references, 'artistic_deviation_id', 'scope artistic deviation references')): membership([getattr(item, attr) for item in references], label)
        identity_pairs=[(item.physical_constraint_id, item.scene_entity_id) for item in s.material_identity_references]
        if any(not constraint_id or not entity_id for constraint_id, entity_id in identity_pairs) or len(identity_pairs) != len(set(identity_pairs)): raise ValueError('Duplicate or blank scope material identity selectors')
        entity_ids=set(s.director_scene_entity_ids); question_ids=set(s.director_physical_question_ids); vt_ids=set(s.director_validation_target_ids)
        if any(not x for x in entity_ids|question_ids|vt_ids): raise ValueError('Blank scope IDs')
        def scope_membership(values, label):
            membership(values, label)
        def scope_pairs(values, label):
            pairs=[(item.entity_id,item.parameter) for item in values]
            if any(not entity or not parameter for entity,parameter in pairs) or len(pairs)!=len(set(pairs)): raise ValueError(f'Duplicate or blank {label}')
        for item in s.physical_constraint_references:
            scope_membership(item.director_scene_entity_ids, 'constraint scope entities'); scope_membership(item.director_physical_question_ids, 'constraint scope questions'); scope_pairs(item.related_material_unknown_parameters, 'constraint scope material pairs')
        for item in s.physical_conflict_references:
            scope_membership(item.physical_constraint_ids, 'conflict scope constraints'); scope_membership(item.director_physical_question_ids, 'conflict scope questions')
        for item in s.unresolved_physical_constraint_references:
            scope_membership(item.director_scene_entity_ids, 'unresolved scope entities'); scope_membership(item.director_physical_question_ids, 'unresolved scope questions'); scope_pairs(item.related_material_unknown_parameters, 'unresolved scope material pairs')
        for item in s.artistic_deviation_references:
            scope_membership(item.director_scene_entity_ids, 'deviation scope entities'); scope_membership(item.director_physical_question_ids, 'deviation scope questions'); scope_pairs(item.related_material_unknown_parameters, 'deviation scope material pairs')
        cr={x.physical_constraint_id:x for x in s.physical_constraint_references}; cf={x.physical_conflict_id:x for x in s.physical_conflict_references}; ur={x.unresolved_physical_constraint_id:x for x in s.unresolved_physical_constraint_references}; ar={x.artistic_deviation_id:x for x in s.artistic_deviation_references}; mi={(x.physical_constraint_id,x.scene_entity_id):x for x in s.material_identity_references}
        if len(cr)!=len(s.physical_constraint_references) or len(cf)!=len(s.physical_conflict_references) or len(ur)!=len(s.unresolved_physical_constraint_references) or len(ar)!=len(s.artistic_deviation_references) or len(mi)!=len(s.material_identity_references): raise ValueError('Duplicate scope references')
        dids=ids(self.decisions,'id','ScenePlanDecision IDs'); pids=ids(self.parameter_assignments,'id','SceneParameterAssignment IDs'); mpids=ids(self.material_plans,'id','SceneMaterialPlan IDs'); depids=ids(self.dependencies,'id','ScenePlanningDependency IDs'); hids=ids(self.validation_hooks,'id','SceneValidationHook IDs'); shotids=ids(self.shot_plan,'id','SceneShotPlan IDs')
        shot_indexes=[x.sequence_index for x in self.shot_plan]
        if len(shot_indexes)!=len(set(shot_indexes)): raise ValueError('Invalid shot sequence indexes')
        unknown_pairs={(x.entity_id,x.parameter) for x in s.director_material_unknown_parameters}
        for d in self.decisions:
            refs(d.target_scene_entity_ids,entity_ids,'decision target entities'); refs(d.basis.director_physical_question_ids,question_ids,'decision physical questions'); refs(d.basis.grounding_constraint_ids,set(cr),'grounding constraints'); refs(d.basis.constraining_constraint_ids,set(cr),'constraining constraints'); refs(d.basis.physical_conflict_ids,set(cf),'decision conflicts'); refs(d.basis.artistic_deviation_ids,set(ar),'decision deviations'); refs(d.basis.unresolved_physical_constraint_ids,set(ur),'decision unresolved'); refs(d.dependency_ids,depids,'decision dependencies')
            if d.status is SceneDecisionStatus.committed and d.dependency_ids: raise ValueError('Committed decision cannot have dependencies')
            if d.status is SceneDecisionStatus.conditional and not d.conditions: raise ValueError('Conditional decision requires conditions')
            if d.kind is SceneDecisionKind.physically_grounded_realization:
                if not d.basis.grounding_constraint_ids: raise ValueError('Grounded decision requires grounding constraint')
                statuses=[cr[x].status for x in d.basis.grounding_constraint_ids]
                if not set(statuses)<= {PhysicalAssessmentStatus.supported,PhysicalAssessmentStatus.conditionally_supported}: raise ValueError('Invalid grounding constraint status')
                if PhysicalAssessmentStatus.conditionally_supported in statuses and d.status is SceneDecisionStatus.committed: raise ValueError('Conditional grounding cannot be committed')
            else:
                if d.basis.grounding_constraint_ids: raise ValueError('Only grounded decision may have grounding constraints')
            if d.kind is SceneDecisionKind.implementation_choice and not d.basis.implementation_rationale: raise ValueError('Implementation choice requires rationale')
            if d.kind is SceneDecisionKind.artistic_deviation_realization and len(d.basis.artistic_deviation_ids)!=1: raise ValueError('Artistic decision requires exactly one deviation')
            if d.kind is SceneDecisionKind.unresolved_dependency_handling and (not d.dependency_ids or d.status is SceneDecisionStatus.committed): raise ValueError('Unresolved handling requires noncommitted dependency')
            for depid in d.dependency_ids:
                dep=next(x for x in self.dependencies if x.id==depid)
                if dep.kind is ScenePlanningDependencyKind.unresolved_physical_constraint and dep.unresolved_physical_constraint_id not in d.basis.unresolved_physical_constraint_ids: raise ValueError('Unresolved dependency must be in decision basis')
                if dep.kind in {ScenePlanningDependencyKind.physical_conflict,ScenePlanningDependencyKind.artist_decision} and dep.physical_conflict_id not in d.basis.physical_conflict_ids: raise ValueError('Conflict dependency must be in decision basis')
                if dep.kind is ScenePlanningDependencyKind.artist_acceptance and dep.artistic_deviation_id not in d.basis.artistic_deviation_ids: raise ValueError('Artist acceptance dependency must be in decision basis')
                if dep.kind is ScenePlanningDependencyKind.material_identity_uncertainty and dep.material_identity_selector.scene_entity_id not in d.target_scene_entity_ids: raise ValueError('Material uncertainty entity must be decision target')
        for dep in self.dependencies:
            populated=sum(x is not None for x in [dep.unresolved_physical_constraint_id,dep.physical_conflict_id,dep.material_identity_selector,dep.artistic_deviation_id])
            if populated!=1: raise ValueError('Dependency requires exactly one subject')
            if dep.kind is ScenePlanningDependencyKind.unresolved_physical_constraint and dep.unresolved_physical_constraint_id not in ur: raise ValueError('Unknown unresolved dependency')
            if dep.kind is ScenePlanningDependencyKind.physical_conflict and dep.physical_conflict_id not in cf: raise ValueError('Unknown conflict dependency')
            if dep.kind is ScenePlanningDependencyKind.artist_decision and (dep.physical_conflict_id not in cf or cf[dep.physical_conflict_id].resolution_status is not PhysicalConflictResolutionStatus.artist_decision_required): raise ValueError('Artist decision requires artist-decision conflict')
            if dep.kind is ScenePlanningDependencyKind.artist_acceptance and (dep.artistic_deviation_id not in ar or not ar[dep.artistic_deviation_id].requires_explicit_artist_acceptance): raise ValueError('Artist acceptance requires accepted deviation')
            if dep.kind is ScenePlanningDependencyKind.material_identity_uncertainty and (dep.material_identity_selector.model_dump() is None or (dep.material_identity_selector.physical_constraint_id,dep.material_identity_selector.scene_entity_id) not in mi or mi[(dep.material_identity_selector.physical_constraint_id,dep.material_identity_selector.scene_entity_id)].status not in {MaterialIdentityStatus.unresolved,MaterialIdentityStatus.contextual_only}): raise ValueError('Invalid material uncertainty dependency')
        established_labels={}
        for identity in s.material_identity_references:
            if identity.status is MaterialIdentityStatus.established_for_scene_entity: established_labels.setdefault(identity.scene_entity_id, set()).add(identity.identity_label)
        if any(len(labels)>1 for labels in established_labels.values()): raise ValueError('Conflicting established material identity labels')
        decisions={x.id:x for x in self.decisions}; deps={x.id:x for x in self.dependencies}
        for decision in self.decisions:
            for conflict_id in decision.basis.physical_conflict_ids:
                conflict = cf[conflict_id]
                matching = [deps[item] for item in decision.dependency_ids if deps[item].physical_conflict_id == conflict_id]
                if conflict.resolution_status is PhysicalConflictResolutionStatus.unresolved:
                    if decision.status is not SceneDecisionStatus.deferred or not any(item.kind is ScenePlanningDependencyKind.physical_conflict for item in matching): raise ValueError('Unresolved conflict requires deferred physical-conflict dependency')
                elif conflict.resolution_status is PhysicalConflictResolutionStatus.context_dependent:
                    if decision.status is SceneDecisionStatus.committed or (decision.status is SceneDecisionStatus.deferred and not any(item.kind is ScenePlanningDependencyKind.physical_conflict for item in matching)): raise ValueError('Context-dependent conflict requires conditional or deferred dependency')
                elif decision.status is SceneDecisionStatus.committed or not any(item.kind is ScenePlanningDependencyKind.artist_decision for item in matching): raise ValueError('Artist-decision conflict requires artist-decision dependency')
        for p in self.parameter_assignments:
            if p.decision_id not in decisions: raise ValueError('Unknown parameter decision')
            d=decisions[p.decision_id]; refs(p.dependency_ids,set(deps),'parameter dependencies')
            if not set(p.dependency_ids)<=set(d.dependency_ids): raise ValueError('Parameter dependencies must be subset of decision dependencies')
            if p.target_scene_entity_id is not None and p.target_scene_entity_id not in d.target_scene_entity_ids: raise ValueError('Parameter target must be decision target')
            if p.category is SceneParameterCategory.material and p.target_scene_entity_id is None: raise ValueError('Material parameter requires target entity')
            required={SceneParameterRole.implementation_choice:SceneDecisionKind.implementation_choice,SceneParameterRole.artistic_realization:SceneDecisionKind.artistic_deviation_realization,SceneParameterRole.provisional_placeholder:SceneDecisionKind.unresolved_dependency_handling,SceneParameterRole.unresolved:SceneDecisionKind.unresolved_dependency_handling}[p.role]
            if d.kind is not required: raise ValueError('Parameter role must match parent decision kind')
            if p.role is SceneParameterRole.unresolved and p.value.kind is not SceneParameterValueKind.unresolved: raise ValueError('Unresolved parameter requires unresolved value')
            if p.role is not SceneParameterRole.unresolved and p.value.kind is SceneParameterValueKind.unresolved: raise ValueError('Concrete parameter role cannot use unresolved value')
            if (p.target_scene_entity_id,p.parameter_name) in unknown_pairs and p.role is SceneParameterRole.implementation_choice: raise ValueError('Director material unknown cannot be ordinary implementation choice')
            if p.role is SceneParameterRole.provisional_placeholder and not any(deps[x].kind in {ScenePlanningDependencyKind.unresolved_physical_constraint,ScenePlanningDependencyKind.material_identity_uncertainty} for x in p.dependency_ids): raise ValueError('Placeholder parameter requires relevant dependency')
        for m in self.material_plans:
            if m.decision_id not in decisions or m.scene_entity_id not in decisions[m.decision_id].target_scene_entity_ids: raise ValueError('Material plan entity must be decision target')
            d=decisions[m.decision_id]; refs(m.dependency_ids,set(deps),'material dependencies')
            if not set(m.dependency_ids)<=set(d.dependency_ids): raise ValueError('Material dependencies must be subset of decision dependencies')
            if m.identity_mode is SceneMaterialIdentityMode.established:
                if not m.material_identity_selector or d.kind is not SceneDecisionKind.physically_grounded_realization: raise ValueError('Established material requires selector and grounded decision')
                ref=mi.get((m.material_identity_selector.physical_constraint_id,m.material_identity_selector.scene_entity_id))
                if not ref or ref.status is not MaterialIdentityStatus.established_for_scene_entity or m.identity_label!=ref.identity_label or ref.physical_constraint_id not in d.basis.grounding_constraint_ids: raise ValueError('Invalid established material plan')
            elif m.identity_mode is SceneMaterialIdentityMode.unresolved_abstract:
                if m.identity_label is not None or d.kind is not SceneDecisionKind.unresolved_dependency_handling: raise ValueError('Invalid unresolved abstract material plan')
            else:
                if not m.identity_label or not m.limitation or d.kind is not SceneDecisionKind.unresolved_dependency_handling or not any(deps[x].kind is ScenePlanningDependencyKind.material_identity_uncertainty for x in m.dependency_ids): raise ValueError('Invalid provisional material plan')
        rid=[x.artistic_deviation_id for x in self.artistic_deviation_realizations]
        if len(rid)!=len(set(rid)) or set(rid)!=set(ar): raise ValueError('Exactly one realization required per artistic deviation')
        seen_art=set()
        for r in self.artistic_deviation_realizations:
            a=ar[r.artistic_deviation_id]; refs(r.decision_ids,dids,'realization decisions'); refs(r.dependency_ids,depids,'realization dependencies')
            if r.deviation_type is not a.deviation_type or r.requires_explicit_artist_acceptance != a.requires_explicit_artist_acceptance or set(r.target_scene_entity_ids)!=set(a.director_scene_entity_ids): raise ValueError('Artistic realization must preserve scoped deviation')
            for did in r.decision_ids:
                d=decisions[did]
                if d.kind is not SceneDecisionKind.artistic_deviation_realization or d.basis.artistic_deviation_ids != [r.artistic_deviation_id] or d.basis.grounding_constraint_ids: raise ValueError('Invalid artistic realization decision')
                seen_art.add(did)
            if a.requires_explicit_artist_acceptance:
                if r.status is SceneDecisionStatus.committed or not r.dependency_ids or not all(d.status is not SceneDecisionStatus.committed and set(r.dependency_ids)<=set(d.dependency_ids) for d in (decisions[x] for x in r.decision_ids)) or not all(deps[x].kind is ScenePlanningDependencyKind.artist_acceptance and deps[x].artistic_deviation_id==r.artistic_deviation_id for x in r.dependency_ids): raise ValueError('Artist acceptance realization must remain conditional/deferred')
        if {d.id for d in self.decisions if d.kind is SceneDecisionKind.artistic_deviation_realization} != seen_art: raise ValueError('Orphan artistic deviation decision')
        global_beat_ids=[beat.id for shot in self.shot_plan for beat in shot.temporal_beats]
        if len(global_beat_ids)!=len(set(global_beat_ids)): raise ValueError('Duplicate TemporalBeat IDs')
        for shot in self.shot_plan:
            refs(shot.decision_ids,dids,'shot decisions'); beat_ids=ids(shot.temporal_beats,'id','TemporalBeat IDs'); beat_indexes=[x.sequence_index for x in shot.temporal_beats]
            if len(beat_indexes)!=len(set(beat_indexes)): raise ValueError('Invalid beat sequence indexes')
            for beat in shot.temporal_beats: refs(beat.decision_ids,set(shot.decision_ids),'beat decisions')
        for hook in self.validation_hooks:
            refs(hook.decision_ids,dids,'hook decisions'); refs(hook.dependency_ids,depids,'hook dependencies'); refs(hook.director_validation_target_ids,vt_ids,'hook validation targets'); refs(hook.physical_constraint_ids,set(cr),'hook constraints'); refs(hook.artistic_deviation_ids,set(ar),'hook deviations'); refs(hook.unresolved_physical_constraint_ids,set(ur),'hook unresolved'); refs(hook.physical_conflict_ids,set(cf),'hook conflicts')
            if hook.kind is SceneValidationHookKind.director_target_check and not hook.director_validation_target_ids: raise ValueError('Director hook needs targets')
            if hook.kind is SceneValidationHookKind.physical_constraint_check and not hook.physical_constraint_ids: raise ValueError('Physical hook needs constraints')
            if hook.kind is SceneValidationHookKind.artistic_deviation_disclosure_check and not hook.artistic_deviation_ids: raise ValueError('Artistic hook needs deviations')
            if hook.kind is SceneValidationHookKind.physical_conflict_check and not hook.physical_conflict_ids: raise ValueError('Conflict hook needs conflicts')
            if hook.kind is SceneValidationHookKind.unresolved_dependency_check:
                if not hook.dependency_ids or not any(deps[x].kind in {ScenePlanningDependencyKind.unresolved_physical_constraint,ScenePlanningDependencyKind.material_identity_uncertainty} for x in hook.dependency_ids): raise ValueError('Unresolved hook needs unresolved/material dependency')
                for x in hook.dependency_ids:
                    if deps[x].kind is ScenePlanningDependencyKind.unresolved_physical_constraint and deps[x].unresolved_physical_constraint_id not in hook.unresolved_physical_constraint_ids: raise ValueError('Unresolved hook must cite exact unresolved ID')
        if not vt_ids <= set().union(*(set(x.director_validation_target_ids) for x in self.validation_hooks if x.kind is SceneValidationHookKind.director_target_check)): raise ValueError('Every Director validation target needs hook')
        cov={(x.subject_kind,x.subject_id):x for x in self.coverage}
        expected={(SceneCoverageSubjectKind.physical_constraint,x) for x in cr}|{(SceneCoverageSubjectKind.physical_conflict,x) for x in cf}|{(SceneCoverageSubjectKind.unresolved_physical_constraint,x) for x in ur}|{(SceneCoverageSubjectKind.artistic_deviation,x) for x in ar}
        if len(cov)!=len(self.coverage) or set(cov)!=expected: raise ValueError('Coverage must be exact')
        for key,c in cov.items():
            refs(c.decision_ids,dids,'coverage decisions'); refs(c.dependency_ids,depids,'coverage dependencies'); refs(c.validation_hook_ids,hids,'coverage hooks')
            if c.state is SceneCoverageState.deferred and not c.reason: raise ValueError('Deferred coverage requires reason')
            if c.subject_kind is SceneCoverageSubjectKind.unresolved_physical_constraint and (c.state is not SceneCoverageState.deferred or not any(deps[x].kind is ScenePlanningDependencyKind.unresolved_physical_constraint and deps[x].unresolved_physical_constraint_id==c.subject_id for x in c.dependency_ids)): raise ValueError('Unresolved coverage requires exact deferred dependency')
            if c.subject_kind is SceneCoverageSubjectKind.artistic_deviation and not any(r.artistic_deviation_id==c.subject_id and set(r.decision_ids)==set(c.decision_ids) for r in self.artistic_deviation_realizations): raise ValueError('Artistic coverage must match realization')
            if c.subject_kind is SceneCoverageSubjectKind.physical_constraint:
                if not any(hook.kind is SceneValidationHookKind.physical_constraint_check and c.subject_id in hook.physical_constraint_ids for hook in self.validation_hooks if hook.id in c.validation_hook_ids): raise ValueError('Constraint coverage needs physical hook')
                if c.state is SceneCoverageState.realized and not any(c.subject_id in decisions[x].basis.grounding_constraint_ids for x in c.decision_ids): raise ValueError('Realized constraint coverage needs grounding decision')
                if c.state is SceneCoverageState.constrains_decision and not any(c.subject_id in decisions[x].basis.constraining_constraint_ids for x in c.decision_ids): raise ValueError('Constraining coverage needs constraining decision')
        for key, c in cov.items():
            if c.subject_kind is SceneCoverageSubjectKind.physical_constraint:
                status=cr[c.subject_id].status
                allowed={PhysicalAssessmentStatus.supported:{SceneCoverageState.realized,SceneCoverageState.constrains_decision,SceneCoverageState.conditional,SceneCoverageState.deferred},PhysicalAssessmentStatus.conditionally_supported:{SceneCoverageState.constrains_decision,SceneCoverageState.conditional,SceneCoverageState.deferred},PhysicalAssessmentStatus.conflicting:{SceneCoverageState.constrains_decision,SceneCoverageState.conditional,SceneCoverageState.deferred},PhysicalAssessmentStatus.unsupported:{SceneCoverageState.constrains_decision,SceneCoverageState.deferred},PhysicalAssessmentStatus.indeterminate:{SceneCoverageState.constrains_decision,SceneCoverageState.deferred}}[status]
                if c.state not in allowed: raise ValueError('Invalid physical constraint coverage state')
                if c.state is SceneCoverageState.conditional and (not c.decision_ids or not all(decisions[item].status is SceneDecisionStatus.conditional and decisions[item].conditions and c.subject_id in (decisions[item].basis.grounding_constraint_ids + decisions[item].basis.constraining_constraint_ids) for item in c.decision_ids)): raise ValueError('Invalid conditional constraint coverage')
            elif c.subject_kind is SceneCoverageSubjectKind.physical_conflict:
                status=cf[c.subject_id].resolution_status; allowed={PhysicalConflictResolutionStatus.unresolved:{SceneCoverageState.deferred},PhysicalConflictResolutionStatus.context_dependent:{SceneCoverageState.conditional,SceneCoverageState.deferred},PhysicalConflictResolutionStatus.artist_decision_required:{SceneCoverageState.conditional,SceneCoverageState.deferred}}[status]
                if c.state not in allowed: raise ValueError('Invalid physical conflict coverage state')
                if not any(h.kind is SceneValidationHookKind.physical_conflict_check and c.subject_id in h.physical_conflict_ids for h in self.validation_hooks if h.id in c.validation_hook_ids): raise ValueError('Conflict coverage needs exact hook')
                required=ScenePlanningDependencyKind.artist_decision if status is PhysicalConflictResolutionStatus.artist_decision_required else ScenePlanningDependencyKind.physical_conflict
                if c.state is SceneCoverageState.deferred and not any(deps[item].kind is required and deps[item].physical_conflict_id==c.subject_id for item in c.dependency_ids): raise ValueError('Deferred conflict needs exact dependency')
                if c.state is SceneCoverageState.conditional and (not c.decision_ids or not all(decisions[item].status is SceneDecisionStatus.conditional and decisions[item].conditions and c.subject_id in decisions[item].basis.physical_conflict_ids for item in c.decision_ids)): raise ValueError('Invalid conditional conflict coverage')
            elif c.subject_kind is SceneCoverageSubjectKind.artistic_deviation:
                if c.state is SceneCoverageState.realized and ar[c.subject_id].requires_explicit_artist_acceptance: raise ValueError('Acceptance-required deviation cannot be realized')
                if not any(h.kind is SceneValidationHookKind.artistic_deviation_disclosure_check and c.subject_id in h.artistic_deviation_ids for h in self.validation_hooks if h.id in c.validation_hook_ids): raise ValueError('Artistic coverage needs exact hook')
        return self
