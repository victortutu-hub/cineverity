"""Deterministic structural tests for Scene Planning Contract v0.1."""
from copy import deepcopy
import json
import pytest
from pydantic import ValidationError
from src.contracts.scene_planning import SceneParameterValue, ScenePlanningContract

H='a'*64; P='b'*64

def payload():
 return {
 'contract_version':'0.1','agent':'scene_planning_agent','input_scope':{
 'director_contract_sha256':H,'physical_constraints_contract_sha256':P,
 'director_scene_entity_ids':['crystal_1'],'director_validation_target_ids':['vt_1'],'director_physical_question_ids':['pq_1'],
 'director_material_unknown_parameters':[{'entity_id':'crystal_1','parameter':'refractive_index'}],
 'physical_constraint_references':[{'physical_constraint_id':'pc_1','status':'supported','director_scene_entity_ids':['crystal_1'],'director_physical_question_ids':['pq_1'],'related_material_unknown_parameters':[]}],
 'physical_conflict_references':[],
 'unresolved_physical_constraint_references':[{'unresolved_physical_constraint_id':'uc_1','director_scene_entity_ids':['crystal_1'],'director_physical_question_ids':['pq_1'],'related_material_unknown_parameters':[{'entity_id':'crystal_1','parameter':'refractive_index'}]}],
 'artistic_deviation_references':[{'artistic_deviation_id':'ad_1','deviation_type':'artistic_amplification','requires_explicit_artist_acceptance':True,'director_scene_entity_ids':['crystal_1'],'director_physical_question_ids':['pq_1'],'related_material_unknown_parameters':[{'entity_id':'crystal_1','parameter':'refractive_index'}]}],
 'material_identity_references':[{'physical_constraint_id':'pc_1','scene_entity_id':'crystal_1','status':'unresolved','identity_label':None}]},
 'decisions':[{'id':'d_ground','kind':'physically_grounded_realization','status':'committed','description':'Grounded qualitative realization.','target_scene_entity_ids':['crystal_1'],'basis':{'director_physical_question_ids':['pq_1'],'grounding_constraint_ids':['pc_1'],'constraining_constraint_ids':[],'physical_conflict_ids':[],'artistic_deviation_ids':[],'unresolved_physical_constraint_ids':[],'implementation_rationale':None},'conditions':[],'dependency_ids':[]},
 {'id':'d_unknown','kind':'unresolved_dependency_handling','status':'deferred','description':'Preserve unknown.','target_scene_entity_ids':['crystal_1'],'basis':{'director_physical_question_ids':['pq_1'],'grounding_constraint_ids':[],'constraining_constraint_ids':[],'physical_conflict_ids':[],'artistic_deviation_ids':[],'unresolved_physical_constraint_ids':['uc_1'],'implementation_rationale':None},'conditions':[],'dependency_ids':['dep_unknown','dep_identity']},
 {'id':'d_art','kind':'artistic_deviation_realization','status':'conditional','description':'Artist decision required.','target_scene_entity_ids':['crystal_1'],'basis':{'director_physical_question_ids':['pq_1'],'grounding_constraint_ids':[],'constraining_constraint_ids':[],'physical_conflict_ids':[],'artistic_deviation_ids':['ad_1'],'unresolved_physical_constraint_ids':[],'implementation_rationale':None},'conditions':['artist accepts'], 'dependency_ids':['dep_accept']}],
 'parameter_assignments':[{'id':'pa_1','decision_id':'d_unknown','target_scene_entity_id':'crystal_1','parameter_name':'refractive_index','category':'material','role':'unresolved','value':{'kind':'unresolved','numeric_value':None,'categorical_value':None,'descriptive_value':None,'boolean_value':None,'unit':None},'dependency_ids':['dep_unknown']}],
 'material_plans':[{'id':'mp_1','decision_id':'d_unknown','scene_entity_id':'crystal_1','identity_mode':'unresolved_abstract','material_identity_selector':None,'identity_label':None,'limitation':None,'dependency_ids':['dep_identity']}],
 'dependencies':[{'id':'dep_unknown','kind':'unresolved_physical_constraint','unresolved_physical_constraint_id':'uc_1','physical_conflict_id':None,'material_identity_selector':None,'artistic_deviation_id':None,'reason':'Missing scene value.'},{'id':'dep_identity','kind':'material_identity_uncertainty','unresolved_physical_constraint_id':None,'physical_conflict_id':None,'material_identity_selector':{'physical_constraint_id':'pc_1','scene_entity_id':'crystal_1'},'artistic_deviation_id':None,'reason':'Identity unknown.'},{'id':'dep_accept','kind':'artist_acceptance','unresolved_physical_constraint_id':None,'physical_conflict_id':None,'material_identity_selector':None,'artistic_deviation_id':'ad_1','reason':'Await acceptance.'}],
 'artistic_deviation_realizations':[{'id':'ar_1','artistic_deviation_id':'ad_1','deviation_type':'artistic_amplification','requires_explicit_artist_acceptance':True,'target_scene_entity_ids':['crystal_1'],'decision_ids':['d_art'],'status':'conditional','dependency_ids':['dep_accept'],'description':'Explicit artistic amplification.'}],
 'shot_plan':[{'id':'shot_1','sequence_index':0,'purpose':'Establish scene.','decision_ids':['d_ground','d_unknown','d_art'],'temporal_beats':[{'id':'beat_1','sequence_index':0,'description':'Reveal.','decision_ids':['d_ground']}]}],
 'validation_hooks':[{'id':'hook_target','kind':'director_target_check','description':'Check target.','decision_ids':['d_ground'],'dependency_ids':[],'director_validation_target_ids':['vt_1'],'physical_constraint_ids':[],'artistic_deviation_ids':[],'unresolved_physical_constraint_ids':[],'physical_conflict_ids':[]},{'id':'hook_pc','kind':'physical_constraint_check','description':'Check constraint.','decision_ids':['d_ground'],'dependency_ids':[],'director_validation_target_ids':[],'physical_constraint_ids':['pc_1'],'artistic_deviation_ids':[],'unresolved_physical_constraint_ids':[],'physical_conflict_ids':[]},{'id':'hook_u','kind':'unresolved_dependency_check','description':'Check uncertainty.','decision_ids':['d_unknown'],'dependency_ids':['dep_unknown','dep_identity'],'director_validation_target_ids':[],'physical_constraint_ids':[],'artistic_deviation_ids':[],'unresolved_physical_constraint_ids':['uc_1'],'physical_conflict_ids':[]},{'id':'hook_a','kind':'artistic_deviation_disclosure_check','description':'Check disclosure.','decision_ids':['d_art'],'dependency_ids':['dep_accept'],'director_validation_target_ids':[],'physical_constraint_ids':[],'artistic_deviation_ids':['ad_1'],'unresolved_physical_constraint_ids':[],'physical_conflict_ids':[]}],
 'coverage':[{'subject_kind':'physical_constraint','subject_id':'pc_1','state':'realized','decision_ids':['d_ground'],'dependency_ids':[],'validation_hook_ids':['hook_pc'],'reason':None},{'subject_kind':'unresolved_physical_constraint','subject_id':'uc_1','state':'deferred','decision_ids':['d_unknown'],'dependency_ids':['dep_unknown'],'validation_hook_ids':['hook_u'],'reason':'Value unresolved.'},{'subject_kind':'artistic_deviation','subject_id':'ad_1','state':'conditional','decision_ids':['d_art'],'dependency_ids':['dep_accept'],'validation_hook_ids':['hook_a'],'reason':None}], 'scene_plan_summary':'Unicode λ μ Å 漢字 preserved.'}

def valid(): return ScenePlanningContract.model_validate(payload())
def invalid(mutator):
 p=payload(); mutator(p)
 with pytest.raises(ValidationError): ScenePlanningContract.model_validate(p)

def test_1_valid_baseline_and_unicode_round_trip():
 m=valid(); assert ScenePlanningContract.model_validate_json(m.model_dump_json()) == m; assert '漢字' in m.scene_plan_summary
@pytest.mark.parametrize('field,value',[('director_contract_sha256','A'*64),('physical_constraints_contract_sha256','a'*63)])
def test_2_3_sha_shape_rejected(field,value): invalid(lambda p:p['input_scope'].__setitem__(field,value))
def test_4_extra_fields_forbidden():
 p=payload(); p['extra']=1
 with pytest.raises(ValidationError): ScenePlanningContract.model_validate(p)
def test_5_unknown_material_cannot_be_ordinary_implementation():
 p=payload(); p['parameter_assignments'][0].update({'decision_id':'d_ground','role':'implementation_choice','value':{'kind':'numeric','numeric_value':'1.5','categorical_value':None,'descriptive_value':None,'boolean_value':None,'unit':None}})
 invalid(lambda x:x.update(p))
def test_6_material_requires_target_entity(): invalid(lambda p:p['parameter_assignments'][0].update({'target_scene_entity_id':None}))
def test_7_committed_dependency_rejected(): invalid(lambda p:p['decisions'][0]['dependency_ids'].append('dep_unknown'))
def test_8_conditional_requires_conditions(): invalid(lambda p:p['decisions'][2].update({'conditions':[]}))
def test_9_grounding_status_unsupported_rejected(): invalid(lambda p:p['input_scope']['physical_constraint_references'][0].update({'status':'unsupported'}))
def test_10_parameter_dependency_subset(): invalid(lambda p:p['parameter_assignments'][0].update({'dependency_ids':['dep_accept']}))
def test_11_material_dependency_subset(): invalid(lambda p:p['material_plans'][0].update({'dependency_ids':['dep_accept']}))
def test_12_unresolved_hook_exact_id(): invalid(lambda p:p['validation_hooks'][2].update({'unresolved_physical_constraint_ids':[]}))
def test_13_coverage_exactness(): invalid(lambda p:p['coverage'].pop())
def test_14_orphan_artistic_decision(): invalid(lambda p:p['artistic_deviation_realizations'][0].update({'decision_ids':[]}))
def test_15_beat_must_be_shot_subset(): invalid(lambda p:p['shot_plan'][0]['temporal_beats'][0].update({'decision_ids':['missing']}))
def test_16_value_exclusivity(): invalid(lambda p:p['parameter_assignments'][0].update({'value':{'kind':'unresolved','numeric_value':'1','categorical_value':None,'descriptive_value':None,'boolean_value':None,'unit':None}}))
def test_17_literals():
 p=payload(); p['agent']='wrong'
 with pytest.raises(ValidationError): ScenePlanningContract.model_validate(p)

@pytest.mark.parametrize("field", ["director_scene_entity_ids", "director_validation_target_ids", "director_physical_question_ids"])
def test_scope_membership_duplicates_rejected(field):
    invalid(lambda p: p["input_scope"][field].append(p["input_scope"][field][0]))


def test_scope_material_unknown_duplicate_rejected():
    invalid(lambda p: p["input_scope"]["director_material_unknown_parameters"].append({"entity_id": "crystal_1", "parameter": "refractive_index"}))


def test_temporal_beat_ids_are_global():
    def mutate(p):
        p["shot_plan"].append({"id":"shot_2", "sequence_index":1, "purpose":"Second.", "decision_ids":["d_ground"], "temporal_beats":[{"id":"beat_1", "sequence_index":0, "description":"Repeat.", "decision_ids":["d_ground"]}]})
    invalid(mutate)


def test_conflicting_established_material_labels_rejected():
    def mutate(p):
        p["input_scope"]["physical_constraint_references"].append({"physical_constraint_id":"pc_2", "status":"supported", "director_scene_entity_ids":["crystal_1"], "director_physical_question_ids":["pq_1"], "related_material_unknown_parameters":[]})
        p["input_scope"]["material_identity_references"] = [
            {"physical_constraint_id":"pc_1", "scene_entity_id":"crystal_1", "status":"established_for_scene_entity", "identity_label":"quartz"},
            {"physical_constraint_id":"pc_2", "scene_entity_id":"crystal_1", "status":"established_for_scene_entity", "identity_label":"diamond"},
        ]
    invalid(mutate)
@pytest.mark.parametrize("field", ["director_scene_entity_ids", "director_physical_question_ids"])
def test_nested_scope_membership_duplicates_rejected(field):
    invalid(lambda p: p["input_scope"]["physical_constraint_references"][0][field].append(p["input_scope"]["physical_constraint_references"][0][field][0]))


@pytest.mark.parametrize("state", ["realized", "conditional"])
def test_unsupported_constraint_coverage_matrix_rejects(state):
    def mutate(p):
        p["input_scope"]["physical_constraint_references"][0]["status"] = "unsupported"
        p["coverage"][0]["state"] = state
    invalid(mutate)


def test_conditional_constraint_coverage_requires_conditional_decision():
    invalid(lambda p: p["coverage"][0].update({"state":"conditional"}))

def test_scene_parameter_value_numeric_rejects_additional_concrete_field():
    with pytest.raises(ValidationError):
        SceneParameterValue.model_validate({"kind": "numeric", "numeric_value": "1.5", "descriptive_value": "commentary"})


def test_scene_parameter_value_categorical_rejects_additional_concrete_field():
    with pytest.raises(ValidationError):
        SceneParameterValue.model_validate({"kind": "categorical", "categorical_value": "GGX", "descriptive_value": "commentary"})


def test_scene_parameter_value_descriptive_rejects_additional_concrete_field():
    with pytest.raises(ValidationError):
        SceneParameterValue.model_validate({"kind": "descriptive", "descriptive_value": "soft", "numeric_value": "1"})


def test_scene_parameter_value_boolean_rejects_additional_concrete_field():
    with pytest.raises(ValidationError):
        SceneParameterValue.model_validate({"kind": "boolean", "boolean_value": True, "descriptive_value": "commentary"})


def test_scene_parameter_value_unresolved_rejects_unit():
    with pytest.raises(ValidationError):
        SceneParameterValue.model_validate({"kind": "unresolved", "unit": "m"})


@pytest.mark.parametrize("numeric_value", ["NaN", "Infinity"])
def test_scene_parameter_value_numeric_rejects_non_finite_decimal(numeric_value):
    with pytest.raises(ValidationError):
        SceneParameterValue.model_validate({"kind": "numeric", "numeric_value": numeric_value})
