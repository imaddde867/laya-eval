from mapping.map_schema import map_schema


def test_boolean_maps_to_noul():
    schema = {"is_urgent": {"type": "boolean", "description": "Is this urgent?"}}
    questions, unmapped = map_schema(schema)
    assert unmapped == []
    assert questions["is_urgent"] == {
        "type": "noul",
        "instructions": "Is this urgent?",
    }


def test_plain_enum_maps_to_choice():
    schema = {
        "category": {
            "type": "enum",
            "description": "Which category?",
            "choices": ["billing", "technical", "sales"],
        }
    }
    questions, unmapped = map_schema(schema)
    assert unmapped == []
    assert questions["category"] == {
        "type": "choice",
        "instructions": "Which category?",
        "criteria": {"billing": "", "technical": "", "sales": ""},
    }


def test_ordered_enum_maps_to_score():
    schema = {
        "severity": {
            "type": "enum",
            "description": "How severe?",
            "choices": ["0", "1", "2", "3"],
            "ordered": True,
        }
    }
    questions, unmapped = map_schema(schema)
    assert unmapped == []
    assert questions["severity"] == {
        "type": "score",
        "instructions": "How severe?",
        "criteria": ["0", "1", "2", "3"],
    }


def test_unknown_type_is_unmapped():
    schema = {
        "tags": {
            "type": "multi-select",
            "description": "Which tags?",
            "choices": ["a", "b"],
        }
    }
    questions, unmapped = map_schema(schema)
    assert unmapped == ["tags"]
    assert questions == {}
