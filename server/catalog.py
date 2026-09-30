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
                "p_yes": {"bucket": .90, "filter": .05, "temperature": .05, "drain": .05, "service": .08},
            },
            {
                "id": "airflow", "prompt": "Can you feel steady airflow at the outlet grille?",
                "instruction": "Keep hands clear of openings; check airflow from outside the grille.",
                "p_yes": {"bucket": .80, "filter": .20, "temperature": .70, "drain": .80, "service": .15},
            },
            {
                "id": "filter_visible", "prompt": "Does the removable filter look covered with dust?",
                "instruction": "Switch the unit off and unplug it before removing the user-serviceable filter.",
                "p_yes": {"bucket": .12, "filter": .88, "temperature": .12, "drain": .12, "service": .18},
            },
            {
                "id": "room_cold", "prompt": "Is the room colder than 18 degrees Celsius or 65 Fahrenheit?",
                "instruction": "Use the room thermostat or a separate thermometer.",
                "p_yes": {"bucket": .10, "filter": .10, "temperature": .85, "drain": .10, "service": .10},
            },
            {
                "id": "hose_kink", "prompt": "If continuous drain is in use, is the hose kinked or rising uphill?",
                "instruction": "Inspect only the exterior hose route. Do not open the appliance cabinet.",
                "p_yes": {"bucket": .05, "filter": .05, "temperature": .05, "drain": .82, "service": .08},
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
                "p_yes": {"load": .85, "level": .15, "transit": .15, "service": .12},
            },
            {
                "id": "rocks", "prompt": "With the machine stopped, does the cabinet rock when pressed at opposite corners?",
                "instruction": "Do not test while the drum is moving.",
                "p_yes": {"load": .10, "level": .82, "transit": .20, "service": .16},
            },
            {
                "id": "new_install", "prompt": "Was the machine installed or moved recently?",
                "instruction": "Answer from the installation history; do not remove any panels.",
                "p_yes": {"load": .18, "level": .18, "transit": .88, "service": .18},
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
