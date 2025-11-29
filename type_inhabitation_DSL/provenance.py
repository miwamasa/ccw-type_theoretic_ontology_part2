# provenance.py
"""
Provenance (来歴) 生成システム

PROV-O (W3C Provenance Ontology) 形式で実行の来歴を記録します。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import json


@dataclass
class ProvenanceGraph:
    """Provenanceグラフ"""
    entities: List[Dict[str, Any]]
    activities: List[Dict[str, Any]]
    agents: List[Dict[str, Any]]
    relations: List[Dict[str, Any]]
    namespaces: Dict[str, str]

    def to_turtle(self) -> str:
        """Turtle (RDF) 形式に変換"""
        lines = []

        # Prefixes
        for prefix, uri in self.namespaces.items():
            lines.append(f"@prefix {prefix}: <{uri}> .")
        lines.append("")

        # Entities
        for entity in self.entities:
            entity_uri = entity['uri']
            lines.append(f"{entity_uri}")
            lines.append(f"  a prov:Entity ;")

            if 'type' in entity:
                lines.append(f"  a {entity['type']} ;")

            if 'value' in entity:
                value = entity['value']
                if isinstance(value, (int, float)):
                    lines.append(f'  prov:value "{value}"^^xsd:double ;')
                else:
                    lines.append(f'  prov:value "{value}" ;')

            if 'attributes' in entity:
                for key, val in entity['attributes'].items():
                    lines.append(f'  ex:{key} "{val}" ;')

            if 'generatedBy' in entity:
                lines.append(f"  prov:wasGeneratedBy {entity['generatedBy']} ;")

            if 'derivedFrom' in entity:
                lines.append(f"  prov:wasDerivedFrom {entity['derivedFrom']} ;")

            # 最後のセミコロンをピリオドに
            if lines[-1].endswith(';'):
                lines[-1] = lines[-1][:-1] + '.'
            lines.append("")

        # Activities
        for activity in self.activities:
            activity_uri = activity['uri']
            lines.append(f"{activity_uri}")
            lines.append(f"  a prov:Activity ;")

            if 'type' in activity:
                lines.append(f"  a {activity['type']} ;")

            if 'label' in activity:
                lines.append(f'  rdfs:label "{activity["label"]}" ;')

            if 'startedAtTime' in activity:
                lines.append(f'  prov:startedAtTime "{activity["startedAtTime"]}"^^xsd:dateTime ;')

            if 'endedAtTime' in activity:
                lines.append(f'  prov:endedAtTime "{activity["endedAtTime"]}"^^xsd:dateTime ;')

            if 'used' in activity:
                for used_entity in activity['used']:
                    lines.append(f"  prov:used {used_entity} ;")

            if 'wasAssociatedWith' in activity:
                lines.append(f"  prov:wasAssociatedWith {activity['wasAssociatedWith']} ;")

            if 'hadPlan' in activity:
                lines.append(f"  prov:hadPlan {activity['hadPlan']} ;")

            if 'attributes' in activity:
                for key, val in activity['attributes'].items():
                    lines.append(f'  ex:{key} "{val}" ;')

            if lines[-1].endswith(';'):
                lines[-1] = lines[-1][:-1] + '.'
            lines.append("")

        # Agents
        for agent in self.agents:
            agent_uri = agent['uri']
            lines.append(f"{agent_uri}")
            lines.append(f"  a prov:Agent ;")

            if 'type' in agent:
                lines.append(f"  a {agent['type']} ;")

            if 'label' in agent:
                lines.append(f'  rdfs:label "{agent["label"]}" ;')

            if 'attributes' in agent:
                for key, val in agent['attributes'].items():
                    lines.append(f'  ex:{key} "{val}" ;')

            if lines[-1].endswith(';'):
                lines[-1] = lines[-1][:-1] + '.'
            lines.append("")

        return '\n'.join(lines)

    def to_json(self) -> str:
        """JSON形式に変換"""
        return json.dumps({
            'entities': self.entities,
            'activities': self.activities,
            'agents': self.agents,
            'relations': self.relations,
            'namespaces': self.namespaces
        }, indent=2, ensure_ascii=False)


class ProvenanceGenerator:
    """Provenance生成器"""

    def __init__(self, base_uri: str = "http://example.org/"):
        self.base_uri = base_uri
        self.namespaces = {
            'prov': 'http://www.w3.org/ns/prov#',
            'ex': base_uri,
            'xsd': 'http://www.w3.org/2001/XMLSchema#',
            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        }

    def generate_from_execution(self, execution_id: str, input_value: Any,
                                output_value: Any, execution_steps: List,
                                context) -> ProvenanceGraph:
        """
        実行結果からProvenanceグラフを生成

        Args:
            execution_id: 実行ID
            input_value: 初期入力値
            output_value: 最終出力値
            execution_steps: ExecutionStepのリスト
            context: ExecutionContext
        """
        entities = []
        activities = []
        agents = []
        relations = []

        # エージェント（システム）
        system_agent = {
            'uri': 'ex:synthesis_system',
            'type': 'prov:SoftwareAgent',
            'label': 'Type-Theoretic Ontology Synthesis System',
            'attributes': {
                'version': '1.0.0'
            }
        }
        agents.append(system_agent)

        # 入力エンティティ
        input_entity = {
            'uri': f'ex:input_{execution_id}',
            'type': 'ex:InputData',
            'value': input_value,
            'attributes': {
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        }
        entities.append(input_entity)

        # 各実行ステップをアクティビティとエンティティに変換
        prev_entity_uri = input_entity['uri']

        for i, step in enumerate(execution_steps):
            step_num = i + 1

            # アクティビティ
            activity = {
                'uri': f'ex:step_{execution_id}_{step_num}',
                'type': 'ex:FunctionExecution',
                'label': f"Execute {step.function_id}",
                'startedAtTime': step.timestamp,
                'endedAtTime': step.timestamp,
                'used': [prev_entity_uri],
                'wasAssociatedWith': 'ex:synthesis_system',
                'attributes': {
                    'function_id': step.function_id,
                    'function_signature': step.function_sig,
                    'implementation_kind': step.impl_kind,
                    'cost': step.impl_details.get('cost', 0),
                    'confidence': step.impl_details.get('confidence', 1.0)
                }
            }

            # パラメータを追加
            if step.parameters_used:
                for key, val in step.parameters_used.items():
                    activity['attributes'][f'param_{key}'] = val

            # データソースを追加
            if step.data_sources:
                activity['attributes']['data_sources'] = ', '.join(step.data_sources)

            activities.append(activity)

            # 出力エンティティ
            output_entity = {
                'uri': f'ex:result_{execution_id}_{step_num}',
                'type': 'ex:IntermediateResult',
                'value': step.output_value,
                'generatedBy': activity['uri'],
                'derivedFrom': prev_entity_uri,
                'attributes': {
                    'timestamp': step.timestamp
                }
            }
            entities.append(output_entity)

            prev_entity_uri = output_entity['uri']

        # 最終出力エンティティ
        final_output = {
            'uri': f'ex:output_{execution_id}',
            'type': 'ex:FinalResult',
            'value': output_value,
            'derivedFrom': prev_entity_uri,
            'attributes': {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'execution_id': execution_id
            }
        }
        entities.append(final_output)

        # 全体の実行プラン
        plan = {
            'uri': f'ex:plan_{execution_id}',
            'type': 'prov:Plan',
            'label': 'Synthesis Plan',
            'attributes': {
                'functions': ' ∘ '.join([s.function_id for s in execution_steps]),
                'total_steps': len(execution_steps)
            }
        }
        entities.append(plan)

        # プランをアクティビティに関連付け
        for activity in activities:
            activity['hadPlan'] = plan['uri']

        return ProvenanceGraph(
            entities=entities,
            activities=activities,
            agents=agents,
            relations=relations,
            namespaces=self.namespaces
        )

    def generate_synthesis_provenance(self, synthesis_id: str, goal: str,
                                     path, input_value: Any,
                                     output_value: Any,
                                     execution_steps: List,
                                     context) -> ProvenanceGraph:
        """
        型合成全体のProvenanceを生成

        より詳細な情報を含む
        """
        prov = self.generate_from_execution(
            synthesis_id, input_value, output_value,
            execution_steps, context
        )

        # 合成目標をエンティティとして追加
        goal_entity = {
            'uri': f'ex:goal_{synthesis_id}',
            'type': 'ex:SynthesisGoal',
            'attributes': {
                'goal_signature': goal,
                'specification': f'Find path from source to target type'
            }
        }
        prov.entities.append(goal_entity)

        # 全体の合成アクティビティ
        synthesis_activity = {
            'uri': f'ex:synthesis_{synthesis_id}',
            'type': 'ex:TypeSynthesis',
            'label': f'Type Synthesis: {goal}',
            'startedAtTime': execution_steps[0].timestamp if execution_steps else datetime.utcnow().isoformat() + 'Z',
            'endedAtTime': execution_steps[-1].timestamp if execution_steps else datetime.utcnow().isoformat() + 'Z',
            'wasAssociatedWith': 'ex:synthesis_system',
            'attributes': {
                'goal': goal,
                'total_cost': sum(s.impl_details.get('cost', 0) for s in execution_steps),
                'path_length': len(execution_steps)
            }
        }
        prov.activities.append(synthesis_activity)

        return prov


# 使用例
if __name__ == '__main__':
    from executor import ExecutionStep
    import uuid

    # ダミーの実行ステップ
    steps = [
        ExecutionStep(
            step_id=str(uuid.uuid4()),
            function_id='usesEnergy',
            function_sig='Product -> Energy',
            input_value=1.0,
            output_value=360000,
            impl_kind='sparql',
            impl_details={'kind': 'sparql', 'cost': 1, 'confidence': 0.9},
            timestamp=datetime.utcnow().isoformat() + 'Z',
            parameters_used={},
            data_sources=['http://example.org/sparql']
        ),
        ExecutionStep(
            step_id=str(uuid.uuid4()),
            function_id='energyToFuelEstimate',
            function_sig='Energy -> Fuel',
            input_value=360000,
            output_value=8.57,
            impl_kind='formula',
            impl_details={'kind': 'formula', 'expr': 'fuel = energy / efficiency', 'cost': 3, 'confidence': 0.8},
            timestamp=datetime.utcnow().isoformat() + 'Z',
            parameters_used={'efficiency': 0.35, 'energy_density': 42e6},
            data_sources=[]
        ),
        ExecutionStep(
            step_id=str(uuid.uuid4()),
            function_id='fuelToCO2',
            function_sig='Fuel -> CO2',
            input_value=8.57,
            output_value=23.14,
            impl_kind='formula',
            impl_details={'kind': 'formula', 'expr': 'co2 = fuel * emission_factor', 'cost': 1, 'confidence': 0.98},
            timestamp=datetime.utcnow().isoformat() + 'Z',
            parameters_used={'emission_factor': 2.7},
            data_sources=[]
        )
    ]

    # Provenance生成
    generator = ProvenanceGenerator()
    prov = generator.generate_synthesis_provenance(
        synthesis_id='test_001',
        goal='Product -> CO2',
        path=None,
        input_value=1.0,
        output_value=23.14,
        execution_steps=steps,
        context=None
    )

    # Turtle形式で出力
    print("# Provenance Graph (Turtle format)")
    print(prov.to_turtle())

    # JSON形式で保存
    with open('provenance_test.json', 'w') as f:
        f.write(prov.to_json())
    print("\nProvenance saved to provenance_test.json")
