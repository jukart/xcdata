settings = {
    "loih": {
        "links": {
            "default.prf": "profiles/loih.prf",
            "Default.tsk": None,
            "airspace1.txt": "airspaces/lovv.desktop.strepla.openair.txt",
            "airspace2.txt": None,
            "waypoint1.cup": "waypoints/Austria.cup",
            "waypoint2.cup": "waypoints/ofm.cup",
            "map.txt": "maps/ALPS_HighRes.xcm",
            "checklist.txt": "checklists/loih.txt",
            "events.xci": "xcsoar/events.xci",
            "plane.xcp": "planes/D-5461-18m.xcp",
            "tasks": "tasks",
        },
        "templates": {
            "templates": {
                "default.prf": "profiles/loih.prf.jinja2",
            },
            "context": {
            }
        },
    },
    "sisteron": {
        "profile": "sisteron.prf",
        "airspace": ["lovv.desktop.strepla.openair.txt"],
        "waipoint": ["ofm.cup"],
        "map": "ALPS_HighRes.xcm",
        "checklist": "sisteron.txt",
        "events": "events.xci",
        "plane": "D-5461-18m.xcp",
    },
    "aac2017": {
        "profile": "wettbewerb.prf",
        "airspace": ["lovv.desktop.strepla.openair.txt"],
        "waipoint": ["Austria.cup", "ofm.cup"],
        "map": "ALPS_HighRes.xcm",
        "checklist": "aac.txt",
        "events": "events.xci",
        "plane": "D-5461-18m.xcp",
    },
    "stm2017": {
        "profile": "wettbewerb.prf",
        "airspace": ["lovv.desktop.strepla.openair.txt"],
        "waipoint": ["Austria.cup", "ofm.cup"],
        "map": "ALPS_HighRes.xcm",
        "checklist": "loih.txt",
        "events": "events.xci",
        "plane": "D-5461-18m.xcp",
    },
}
