# This file contains the code of searching a valid instanciated template and expanding the templates
import random
from typing import Dict, List, Optional, Tuple

import question_engine as qeng
from custom_types import (Answer_Counts, Metadata, Node, Scene_Struct, State,
                          Template)
from filters import (add_empty_filter_options, derive_cf_attributes,
                     derive_cf_relations, find_filter_options,
                     find_relate_filter_options)
from utils import node_shallow_copy


def do_dfs(template: Template, metadata: Metadata, scene_struct: Scene_Struct, verbose: bool, answer_counts: Answer_Counts, max_instances: Optional[int], final_filters=None) -> Tuple[Dict[str, List[Node]], List[State]]:
  param_name_to_type = {p['name']: p['type'] for p in template['params']} 

  # initial_state: State = {
  initial_state: State = {  # type: ignore    
    'nodes': [node_shallow_copy(template['nodes'][0])],
    'vals': {},
    'input_map': {0: 0},
    'next_template_node': 1,
  }
  states = [initial_state]
  final_states = []
  state_iter = 0
  dfs_mode = final_filters is None
  while states:
    state = states.pop()
    if verbose:
      # print(f"Processing state {state_iter}: {state}")
      state_iter = state_iter + 1
    
    # Check to make sure the current state is valid
    q = {'nodes': state['nodes']}
    outputs = qeng.answer_question(q, metadata, scene_struct, all_outputs=True)
    answer = outputs[-1]
    if answer == '__INVALID__': continue

    # Check to make sure constraints are satisfied for the current state
    skip_state = False
    for constraint in template['constraints']:
      if not dfs_mode:
        # do not evaluate constraints during non dfs mode
        pass
      elif constraint['type'] == 'NEQ':
        p1, p2 = constraint['params']
        v1, v2 = state['vals'].get(p1), state['vals'].get(p2)
        if v1 is not None and v2 is not None and v1 != v2:
          if verbose:
            print('skipping due to NEQ constraint')
            print(constraint)
            print(state['vals'])
          skip_state = True
          break
      elif constraint['type'] == 'NULL':
        p = constraint['params'][0]
        p_type = param_name_to_type[p]
        v = state['vals'].get(p)
        if v is not None:
          if v not in ["", "thing"]:
            if verbose:
              print('skipping due to NULL constraint')
              print(constraint)
              print(state['vals'])
            skip_state = True
            break
      elif constraint['type'] == 'OUT_NEQ':
        i, j = constraint['params']
        i = state['input_map'].get(i, None)
        j = state['input_map'].get(j, None)
        if i is not None and j is not None and outputs[i] == outputs[j]:
          if verbose:
            print('skipping due to OUT_NEQ constraint')
            print(outputs[i])
            print(outputs[j])
          skip_state = True
          break
      else:
        assert False, 'Unrecognized constraint type "%s"' % constraint['type']

    if skip_state:
      continue

    # We have already checked to make sure the answer is valid, so if we have
    # processed all the nodes in the template then the current state is a valid
    # question, so add it if it passes our rejection sampling tests.
    if state['next_template_node'] == len(template['nodes']) and dfs_mode:
      # Use our rejection sampling heuristics to decide whether we should
      # keep this template instantiation
      cur_answer_count = answer_counts[answer]
      answer_counts_sorted = sorted(answer_counts.values())
      median_count = answer_counts_sorted[len(answer_counts_sorted) // 2]
      median_count = max(median_count, 5)
      if cur_answer_count > 1.1 * answer_counts_sorted[-2]:
        if verbose: print('skipping due to second count')
        continue
      if cur_answer_count > 5.0 * median_count:
        if verbose: print('skipping due to median')
        continue

      # If the template contains a raw relate node then we need to check for
      # degeneracy at the end
      has_relate = any(n['type'] == 'relate' for n in template['nodes'])
      if has_relate:
        degen = qeng.is_degenerate(q, metadata, scene_struct, answer=answer,
                                   verbose=verbose)
        if degen:
          continue

      answer_counts[answer] += 1

    if state['next_template_node'] == len(template['nodes']):
      # This basically checks whether we have reached the end of the program specified in nodes.
      # this has almost the same check as the if above, but has to be run, regardless whether we generate answers or explanations  
      state['answer'] = answer  # type: ignore
      final_states.append(state)
      if max_instances is not None and len(final_states) == max_instances and dfs_mode:
        break
      continue

    # Otherwise fetch the next node from the template
    # Make a shallow copy so cached _outputs don't leak ... this is very nasty
    next_node = template['nodes'][state['next_template_node']]
    next_node = node_shallow_copy(next_node)

    special_nodes = {
        'filter_unique', 'filter_count', 'filter_qa_count', 'filter_exist', 'filter',
        'relate_filter', 'relate_filter_unique', 'relate_filter_count',
        'relate_filter_exist', 'relate',
    }
    if next_node['type'] in special_nodes or (next_node["type"] in ['filter_size', 'filter_color', 'filter_material', 'filter_shape'] and not dfs_mode):
      if next_node['type'].startswith('relate_filter'):
        # Don't compute this, if we are in cf explanation mode, bc. find_relate_filter_options is not able to deal with List[List[]]
        if dfs_mode:
        # TODO: Find the cleanest way to split the normal do_dfs and the cf explanation do_dfs?
          unique = (next_node['type'] == 'relate_filter_unique')
          include_zero = (next_node['type'] == 'relate_filter_count'
                          or next_node['type'] == 'relate_filter_exist')
          filter_options = find_relate_filter_options(answer, scene_struct, metadata, unique=unique, include_zero=include_zero)
      elif next_node['type'].startswith('relate'):
        if dfs_mode:
          # repeat whats happing at side info (down below)
          filter_options = {(k,()): [] for k in ["left", "right", "front", "behind"]}
          pass
      else:
        filter_options = find_filter_options(answer, scene_struct, metadata)
        if next_node['type'] == 'filter':
          # Remove null filter
          filter_options.pop((None, None, None, None), None)
        if next_node['type'] == 'filter_unique':
          # Get rid of all filter options that don't result in a single object
          filter_options = {k: v for k, v in filter_options.items()
                            if len(v) == 1}
        else:
          # Add some filter options that do NOT correspond to the scene
          if next_node['type'] == 'filter_exist':
            # For filter_exist we want an equal number that do and don't
            num_to_add = len(filter_options)
          elif next_node['type'] in ['filter_qa_count', 'filter_count', 'filter', 'filter_size', 'filter_color', 'filter_material', 'filter_shape']:
            # For filter_count add nulls equal to the number of singletons
            num_to_add = sum(1 for k, v in filter_options.items() if len(v) == 1)
          add_empty_filter_options(filter_options, metadata, num_to_add)

      # Overwrite filter_option_keys with an external parameter, if we already have the final state and only want to do a counter factual explanation
      if dfs_mode:
        filter_option_keys = list(filter_options.keys())
        random.shuffle(filter_option_keys)
      else:
        # create Almost Matching filters, to get the objects which almost match to the original filter
        current_final_filters = tuple(final_filters[si] for si in next_node["side_inputs"])
        
        if any(["R" in si for si in next_node["side_inputs"]]):
          # case with relations, this means that there is a relation which needs to be prepended (relation, (attr1, attr2, ...))
          filter_option_keys = derive_cf_relations(current_final_filters)
        else:
          # case with only attributes
          filter_option_keys = derive_cf_attributes(current_final_filters)  # type: ignore

        # if verbose: print(filter_option_keys)

      for k in filter_option_keys:
        new_nodes = []
        cur_next_vals = {k: v for k, v in state['vals'].items()}
        next_input = state['input_map'][next_node['inputs'][0]]
        filter_side_inputs = next_node['side_inputs']
        if next_node['type'].startswith('relate'):
          param_name = next_node['side_inputs'][0] # First one should be relate
          filter_side_inputs = next_node['side_inputs'][1:]
          param_type = param_name_to_type[param_name]
          assert param_type == 'Relation'
          param_val = k[0]
          k = k[1]
          new_nodes.append({
            'type': 'relate',
            'inputs': [next_input],
            'side_inputs': [param_val],
          })
          cur_next_vals[param_name] = param_val
          next_input = len(state['nodes']) + len(new_nodes) - 1
        for param_name, param_val in zip(filter_side_inputs, k):
          param_type = param_name_to_type[param_name]
          filter_type = 'filter_%s' % param_type.lower()
          if param_val is not None:
            new_nodes.append({
              'type': filter_type,
              'inputs': [next_input],
              'side_inputs': [param_val],
            })
            cur_next_vals[param_name] = param_val
            next_input = len(state['nodes']) + len(new_nodes) - 1
          elif param_val is None:
            if metadata['dataset'] == 'CLEVR-v1.0' and param_type == 'Shape':
              param_val = 'thing'
            else:
              param_val = ''
            cur_next_vals[param_name] = param_val
        input_map = {k: v for k, v in state['input_map'].items()}
        extra_type = None
        if next_node['type'].endswith('unique'):
          extra_type = 'unique'
        if next_node['type'].endswith('count'):
          extra_type = 'count'
        if next_node['type'].endswith('exist'):
          extra_type = 'exist'
        if extra_type is not None:
          new_nodes.append({
            'type': extra_type,
            'inputs': [input_map[next_node['inputs'][0]] + len(new_nodes)],
          })
        input_map[state['next_template_node']] = len(state['nodes']) + len(new_nodes) - 1
        states.append({  # type: ignore
          'nodes': state['nodes'] + new_nodes,
          'vals': cur_next_vals,
          'input_map': input_map,
          'next_template_node': state['next_template_node'] + 1,
        })

    elif 'side_inputs' in next_node:
      # If the next node has template parameters, expand them out
      # TODO: Generalize this to work for nodes with more than one side input
      assert len(next_node['side_inputs']) == 1, 'NOT IMPLEMENTED'

      # Use metadata to figure out domain of valid values for this parameter.
      # Iterate over the values in a random order; then it is safe to bail
      # from the DFS as soon as we find the desired number of valid template
      # instantiations.
      param_name = next_node['side_inputs'][0]
      param_type = param_name_to_type[param_name]
      param_vals = metadata['types'][param_type][:]
      random.shuffle(param_vals)
      for val in param_vals:
        input_map = {k: v for k, v in state['input_map'].items()}
        input_map[state['next_template_node']] = len(state['nodes'])
        cur_next_node = {
          'type': next_node['type'],
          'inputs': [input_map[idx] for idx in next_node['inputs']],
          'side_inputs': [val],
        }
        cur_next_vals = {k: v for k, v in state['vals'].items()}
        cur_next_vals[param_name] = val

        states.append({  # type: ignore
          'nodes': state['nodes'] + [cur_next_node],
          'vals': cur_next_vals,
          'input_map': input_map,
          'next_template_node': state['next_template_node'] + 1,
        })
    else:
      input_map = {k: v for k, v in state['input_map'].items()}
      input_map[state['next_template_node']] = len(state['nodes'])
      _output = next_node.get("_output")
      next_node = {
        'type': next_node['type'],
        'inputs': [input_map[idx] for idx in next_node['inputs']],
      }
      if _output is not None:
        next_node["_output"] = _output

      states.append({ # type: ignore
        'nodes': state['nodes'] + [next_node],
        'vals': state['vals'],
        'input_map': input_map,
        'next_template_node': state['next_template_node'] + 1,
      })
  return q, final_states
