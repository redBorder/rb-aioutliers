# query_builder.py

def granularity_to_seconds(granularity):
    """
    Get the number of seconds for each possible druid
    granularity. For example, "pt2m" would return 120
    and "thirty_minute" would return 1800.

    Args:
        -granularity (string): druid granularity.
    Returns:
        - (int): number of seconds in the granularity.
    """
    base_granularities = {
        "minute": 60, "hour": 3600, "day": 86400,
        "fifteen_minute": 900, "thirty_minute": 1800,
        "m": 60, "h": 3600, "d": 86400
    }
    granularity = granularity.lower()
    if granularity in base_granularities.keys():
        return base_granularities[granularity]
    else:
        numbers = int(''.join(filter(str.isdigit, granularity)))
    return numbers * base_granularities[granularity[-1]]

def modify_aggregations(query):
    """
    Modify a druid query to add every field the traffic module uses.
    Those are: "bytes", "pkts", "clients", "flows", "bps", "pps", "fps",
    "bytes_per_client" , "bytes_per_sec_per_client", "flows_per_client" 
    and "flows_per_sec_per_client".
    
    Args:
        -query: dicitionary with the druid query.
    Returns:
        -query: the modified query.
    """
    granularity = query.get("granularity", {}).get("period", "minute")
    spg = granularity_to_seconds(granularity)
    query["aggregations"] = [
        {"type": "longSum", "name": "bytes", "fieldName": "sum_bytes"},
        {"type": "longSum", "name": "pkts", "fieldName": "sum_pkts"},
        {"type": "hyperUnique", "name": "clients", "fieldName": "clients"},
        {"type": "longSum", "name": "flows", "fieldName": "events"}
    ]
    query["postAggregations"] = [
        {"type": "arithmetic", "name": "bps", "fn": "/",
         "fields": [{"type": "arithmetic", "name": "bits", "fn": "*",
                     "fields": [{"type": "fieldAccess", "fieldName": "bytes"}, {"type": "constant", "value": 8}]},
                    {"type": "constant", "value": spg}]},
        {"type": "arithmetic", "name": "pps", "fn": "/",
         "fields": [{"type": "fieldAccess", "fieldName": "pkts"}, {"type": "constant", "value": spg}]},
        {"type": "arithmetic", "name": "fps", "fn": "/",
         "fields": [{"type": "fieldAccess", "name": "flows", "fieldName": "flows"}, {"type": "constant", "value": spg}]},
        {"type": "arithmetic", "name": "bytes_per_client", "fn": "/",
         "fields": [{"type": "fieldAccess", "name": "bytes", "fieldName": "bytes"},
                    {"type": "hyperUniqueCardinality", "fieldName": "clients"}]},
        {"type": "arithmetic", "name": "bits_per_sec_per_client", "fn": "/",
         "fields": [{"type": "arithmetic", "name": "bps", "fn": "/",
                     "fields": [{"type": "arithmetic", "name": "bits", "fn": "*",
                                 "fields": [{"type": "fieldAccess", "fieldName": "bytes"}, {"type": "constant", "value": 8}]},
                                {"type": "constant", "value": spg}]},
                    {"type": "hyperUniqueCardinality", "fieldName": "clients"}]},
        {"type": "arithmetic", "name": "flows_per_client", "fn": "/",
         "fields": [{"type": "fieldAccess", "name": "flows", "fieldName": "flows"},
                    {"type": "hyperUniqueCardinality", "fieldName": "clients"}]},
        {"type": "arithmetic", "name": "flows_per_sec_per_client", "fn": "/",
         "fields": [{"type": "arithmetic", "name": "fps", "fn": "/",
                     "fields": [{"type": "fieldAccess", "name": "flows", "fieldName": "flows"},
                                {"type": "constant", "value": spg}]},
                    {"type": "hyperUniqueCardinality", "fieldName": "clients"}]}
    ]
    return query