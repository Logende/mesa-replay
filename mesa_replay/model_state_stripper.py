import dill


def strip_off_unneeded_data_from_model_dict(original_model_dict: dict):
    """If not overwritten by custom serialization, CacheableModel persists the complete 'model.__dict__' for every step.
    Not everything that the model dict contains needs to be cached. As most model properties are model-specific, the
    decision of what to store and what not to store is up to the person developing the model, which they can do by
    overwriting the 'CacheableModel._serialize_state' function. Some generic optimization, however, can be made:
    Many mesa models use the mesa scheduling and/or the mesa datacollector functionality. The scheduler does not need to
    be cached, therefore, we can remove it. The datacollector stores not only data from the current, but also from the
    previous steps. This we can change, by deleting all data from the previous steps. That is exactly what this function
    does. The original dict of the model is taken as input, copied and then unneeded data is removed from the copy. This
    stripped copy is then returned."""
    dict_copy = dill.copy(original_model_dict)
    dict_copy["schedule"] = None
    if "datacollector" in dict_copy:
        data_collector = dict_copy["datacollector"]

        model_vars: dict = data_collector.model_vars
        for key in model_vars.keys():
            values_list: list = model_vars[key]
            latest_value = values_list[len(values_list) - 1]
            model_vars[key] = [latest_value]

        agent_records: dict = data_collector._agent_records
        if not len(agent_records) == 0:
            latest_agent_record_key = len(agent_records) - 1
            latest_agent_record_value = agent_records[latest_agent_record_key]
            data_collector._agent_records = {
                latest_agent_record_key: latest_agent_record_value
            }

    return dict_copy
