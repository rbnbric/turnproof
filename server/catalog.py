"""Small, inspectable diagnostic catalog used by the proof of concept."""

SCENARIOS = {
    "dehumidifier": {
        "label": "Dehumidifier not collecting water",
        "causes": {
            "bucket": {"label": "Bucket is full or mis-seated", "prior": 28},
            "filter": {"label": "Air filter is obstructed", "prior": 24},
            "temperature": {"label": "Room is too cold for normal operation", "prior": 18},
            "drain": {"label": "Continuous-drain hose is blocked", "prior": 16},
            "service": {"label": "Fan, sensor, or refrigeration fault", "prior": 14},
        },
        "checks": [
            {
                "id": "bucket_light", "prompt": "Is the bucket-full light on?",
                "instruction": "Look at the control panel without opening the appliance.",
                "effects": {"yes": {"bucket": 4.0}, "no": {"bucket": 0.35}},
                "priority": 100,
            },
            {
                "id": "airflow", "prompt": "Can you feel steady airflow at the outlet grille?",
                "instruction": "Keep hands clear of openings; check airflow from outside the grille.",
                "effects": {"yes": {"filter": 0.55, "service": 0.55}, "no": {"filter": 2.2, "service": 2.6}},
                "priority": 90,
            },
            {
                "id": "filter_visible", "prompt": "Does the removable filter look covered with dust?",
                "instruction": "Switch the unit off and unplug it before removing the user-serviceable filter.",
                "effects": {"yes": {"filter": 4.0}, "no": {"filter": 0.3}},
                "priority": 80,
            },
            {
                "id": "room_cold", "prompt": "Is the room colder than 18 degrees Celsius or 65 Fahrenheit?",
                "instruction": "Use the room thermostat or a separate thermometer.",
                "effects": {"yes": {"temperature": 4.0}, "no": {"temperature": 0.3}},
                "priority": 70,
            },
            {
                "id": "hose_kink", "prompt": "If continuous drain is in use, is the hose kinked or rising uphill?",
                "instruction": "Inspect only the exterior hose route. Do not open the appliance cabinet.",
                "effects": {"yes": {"drain": 4.0}, "no": {"drain": 0.5}},
                "priority": 60,
            },
        ],
        "resolutions": {
            "bucket": "Power off the unit, reseat the bucket, and confirm the float moves freely.",
            "filter": "Clean the user-serviceable filter as the manufacturer directs, then retest.",
            "temperature": "Move or pause the unit until the room is within its rated operating temperature.",
            "drain": "Route the external drain hose continuously downhill and remove visible kinks.",
            "service": "Stop the test and arrange qualified service; the remaining causes require internal diagnosis.",
        },
    },
    "washer": {
        "label": "Washing machine banging during spin",
        "causes": {
            "load": {"label": "Load is unbalanced", "prior": 45},
            "level": {"label": "Machine is not level", "prior": 30},
            "transit": {"label": "Shipping bolts remain installed", "prior": 15},
            "service": {"label": "Suspension or bearing fault", "prior": 10},
        },
        "checks": [
            {
                "id": "single_item", "prompt": "Is the load one heavy item or gathered on one side?",
                "instruction": "Pause the cycle before inspecting the drum.",
                "effects": {"yes": {"load": 4.0}, "no": {"load": 0.35}}, "priority": 100,
            },
            {
                "id": "rocks", "prompt": "With the machine stopped, does the cabinet rock when pressed at opposite corners?",
                "instruction": "Do not test while the drum is moving.",
                "effects": {"yes": {"level": 4.0}, "no": {"level": 0.4}}, "priority": 90,
            },
            {
                "id": "new_install", "prompt": "Was the machine installed or moved recently?",
                "instruction": "Answer from the installation history; do not remove any panels.",
                "effects": {"yes": {"transit": 3.5}, "no": {"transit": 0.4}}, "priority": 80,
            },
        ],
        "resolutions": {
            "load": "Pause, redistribute the load evenly, and restart at a lower spin speed.",
            "level": "Level the machine using the manufacturer procedure and verify all feet are firm.",
            "transit": "Do not run another spin cycle until the installation guide confirms shipping hardware is removed.",
            "service": "Stop using high-speed spin and arrange qualified service for the suspension or bearings.",
        },
    },
}

HAZARD_TERMS = {
    "smoke", "sparks", "burning", "gas smell", "electrical shock", "flames", "scorched"
}

