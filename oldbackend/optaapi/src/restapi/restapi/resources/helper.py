from src.feedAPI.EventAPI import EventAPI


def separate_raw_string(raw_string, character):
    result = list()

    for block in str(raw_string).split(str(character)):
        block = block.strip()
        if block != "":
            result.append(block)

    if len(result) == 0:
        return None
    else:
        return result


def separate_raw_string_into_integers(raw_string, character):
    result = list()

    for block in str(raw_string).split(str(character)):
        block = block.strip()
        if block != "":
            result.append(int(block))

    if len(result) == 0:
        return None
    else:
        return result


def translate_list_items_wrt_dict(the_list, the_dict):
    if the_dict:
        if type(the_list) not in [list, tuple]:
            the_list = list(the_list)

        translated_list = list()
        try:
            for term in the_list:
                translated_list.append(the_dict[term])
        except KeyError:
            return None
        return translated_list
    else:
        return None


def convert_raw_string_into_bool(raw_string):
    if raw_string:
        if str(raw_string).strip().lower() in ["1", "ok", "true", "yes"]:
            return True
        else:
            return False
    else:
        return False


def check_events_existence(event_names):
    if event_names:
        if type(event_names) not in [list, tuple]:
            event_name_list = list()
            event_name_list.append(event_names)
        else:
            event_name_list = event_names
    else:
        return True

    all_existing_events = set(list(EventAPI().getEventDict().keys()))
    all_events_to_check = set(event_name_list)

    if all_events_to_check.issubset(all_existing_events):
        return True
    else:
        return False


def check_event_params_existence(event_name, event_params):
    if event_name:
        if type(event_name) not in [list, tuple]:
            event_name_list = list()
            event_name_list.append(event_name)
        else:
            event_name_list = event_name
    else:
        event_name_list = list(EventAPI().getEventDict().keys())

    if event_params:
        if type(event_params) not in [list, tuple]:
            event_params_list = list()
            event_params_list.append(event_params)
        else:
            event_params_list = event_params
    else:
        return True

    all_existing_event_params = set()
    for event_name in event_name_list:
        temp_set = set(EventAPI().getEventParams(event_name))
        all_existing_event_params.union(temp_set)

    all_event_params_to_check = set(event_params_list)

    if all_event_params_to_check.issubset(all_existing_event_params):
        return True
    else:
        return False


def get_rid_of_inner_lists(results):
    if hasattr(results, "__iter__"):
        all_possible_events = list(EventAPI().getEventDict().keys())
        for document in results:
            if isinstance(document, dict):
                for key, value in document.items():
                    if key in all_possible_events:
                        if isinstance(value, list):
                            if len(value) == 1:
                                document[key] = value[0]
        return results


# Following function will convert a given string from URL request argument,
# transforms it into a pipeline readable statement for mongoengine operations.
# Example: "card_event.yellow_card > 7 " ----> {'card_event.yellow_card': {'$gte': 7.0}}
def mongodb_query_converter(raw_query_string):
    operations_one_char = {
        "=": "$eq",
        ">": "$gt",
        "<": "$lt",
    }

    operations_two_char = {
        "!=": "$ne",
        ">=": "$gte",
        "<=": "$lte"
    }

    query_condition_dict = {
        "and": list(),
        "or": list()
    }

    all_operations = {**operations_two_char, **operations_one_char}
    all_operation_chars = list(operations_two_char.keys()) + list(operations_one_char.keys())

    for condition in raw_query_string.split(","):

        condition_logic = condition.split(":")[0].strip().lower()
        if condition_logic not in query_condition_dict.keys():
            condition_logic = "and"
        condition = condition.split(":")[-1].strip()
        flag_there_is_no_operation_char = True
        for operations_char in all_operation_chars:
            if operations_char in condition:
                temp_query = dict()
                temp_key = condition.split(operations_char)[0].strip()
                try:
                    temp_value = {all_operations[operations_char]: float(condition.split(operations_char)[1].strip())}
                except ValueError:
                    temp_value = {all_operations[operations_char]: str(condition.split(operations_char)[1].strip())}

                if temp_value not in [None, ""]:
                    temp_query[temp_key] = temp_value
                    query_condition_dict[condition_logic] += [temp_query]
                    flag_there_is_no_operation_char = False
                    break

        if flag_there_is_no_operation_char and condition not in [None, ""]:
            existing_conditions = [None, list(), str()]
            for existing_condition in existing_conditions:
                temp_query = {condition: {"$ne": existing_condition}}
                query_condition_dict[condition_logic] += [temp_query]

    query = dict()

    for key in query_condition_dict.keys():
        temp_query_combination_list = query_condition_dict[key]
        if temp_query_combination_list != list():
            query["$"+key] = temp_query_combination_list

    if query == dict():
        return None

    return query


# Following function will convert a given string from URL request argument,
# transforms it into a pipeline readable statement for mongoengine operations.
# Example: "card_event.yellow_card:desc" ----> {"card_event.yellow_card: -1}
def mongodb_sort_query_converter(raw_string):
    sort_query_dict = dict()

    for condition in raw_string.split(","):
        condition = condition.strip()
        condition_list = condition.split(":")

        if len(condition_list) == 1:
            temp_condition = condition_list[0].strip()
            sort_query_dict[temp_condition] = 1

        elif len(condition_list) == 2:
            temp_condition = condition_list[0].strip()
            if condition_list[1].strip().lower() in ["-1", "descending", "desc"]:
                sort_query_dict[temp_condition] = -1
            else:
                sort_query_dict[temp_condition] = 1

        else:
            return None

    return sort_query_dict


def mongodb_logic_operation_query_converter(raw_string):
    logic_operation = "and"
    if raw_string:
        if raw_string.strip().lower() in ["or"]:
            logic_operation = "or"

    return logic_operation


def mongodb_limit_query_converter(raw_string):
    if raw_string:
        try:
            limit = int(raw_string.strip())
            return limit
        except ValueError:
            return None


def mongodb_time_query_converter(raw_string=None, return_time_interval=True,
                                 return_time_query=False, raw_time_interval=None):
    if raw_string:

        time_interval = {
            "from": {
                "min": None,
                "sec": 0,
                "period": 1
            },

            "to": {
                "min": None,
                "sec": 0,
                "period": 2
            }
        }
        raw_string = str(raw_string).strip()
        possible_chars = [",", ":", ";", "/"]
        for char in possible_chars:
            raw_string = raw_string.replace(char, ".")

        time_info_list = raw_string.split("-")
        from_or_to_flag = "from"
        for time_info in time_info_list:

            if time_info.strip() != str():
                if time_interval["from"]["min"] is not None:
                    from_or_to_flag = "to"

                if "^" in time_info:
                    period = int(time_info.split("^")[0])
                    time_interval[from_or_to_flag]["period"] = period
                    time_info = str(time_info.split("^")[-1]).strip()
                    if time_info == str():
                        continue

                for min_sec in time_info.split("."):
                    if min_sec.strip() != str():

                        if from_or_to_flag == "from":
                            if time_interval["from"]["min"] is None:
                                time_interval["from"]["min"] = int(min_sec.strip())

                            else:
                                time_interval["from"]["sec"] = int(min_sec.strip())
                                break

                        elif from_or_to_flag == "to":
                            if time_interval["to"]["min"] is None:
                                time_interval["to"]["min"] = int(min_sec.strip())

                            else:
                                time_interval["to"]["sec"] = int(min_sec.strip())
                                break
    elif raw_time_interval:
        time_interval = raw_time_interval

    else:
        print("Both 'raw_string' and 'raw_time_interval' can not be empty at the same time.")
        return None

    time_query_or = list()

    if time_interval["from"]["min"] is not None and time_interval["to"]["min"] is not None:
        time_query_or.append({"events.min": {"$gt": int(time_interval["from"]["min"]),
                                             "$lt": int(time_interval["to"]["min"])}})
        time_query_or.append({"events.min": {"$eq": int(time_interval["from"]["min"])},
                              "events.sec": {"$gte": int(time_interval["from"]["sec"])}})
        time_query_or.append({"events.min": {"$eq": int(time_interval["to"]["min"])},
                              "events.sec": {"$lte": int(time_interval["to"]["sec"])}})
        time_query = {
            "$and": [{"events.periodID": {"$gte": int(time_interval["from"]["period"]),
                                          "$lte": int(time_interval["to"]["period"])}},
                     {"$or": time_query_or}]
        }

    if return_time_interval:
        return time_interval
    elif return_time_query:
        return time_query
    else:
        return None


def inverse_of_mongo_db_time_query_converter(time_interval):
    if time_interval:
        try:
            condition = str(time_interval["from"]["min"]) is None or str(time_interval["to"]["min"]) is None
            if condition:
                print("The time interval does not have proper minute data!")
                return None

            time_string = str()
            for from_to in ["from", "to"]:
                time_string += str(time_interval[from_to]["period"]) + "^"
                time_string += str(time_interval[from_to]["min"]) + ":"
                time_string += str(time_interval[from_to]["sec"]) + "-"
            return time_string
        except KeyError:
            print("Given input dictionary does not have proper keys, try to use mongodb_time_query_converter().")
            return None


def length_of_time_interval_obtained_from_converter(time_interval):
    if time_interval:
        try:
            if time_interval["from"]["min"] is None:
                time_interval["from"]["min"] = 0
            if time_interval["from"]["sec"] is None:
                time_interval["from"]["sec"] = 0
            if time_interval["to"]["min"] is None:
                time_interval["to"]["min"] = 90
            if time_interval["to"]["sec"] is None:
                time_interval["to"]["sec"] = 0

            from_minute = float(time_interval["from"]["min"]) + float((time_interval["from"]["sec"])/60)
            to_minute = float(time_interval["to"]["min"]) + float((time_interval["to"]["sec"]) / 60)

            return to_minute - from_minute

        except KeyError:
            print("Given input dictionary does not have proper keys, try to use mongodb_time_query_converter().")
            return None



