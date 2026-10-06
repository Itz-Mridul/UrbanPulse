"""
Kedarnath 2013 — Historical Replay Data
=========================================
Synthetic reconstruction of the pre-event timeline leading up to
the Kedarnath cloudburst + glacial lake outburst flood, June 2013.

Source: Dobhal et al. (2013), Zainuddin et al. (2020), IMD records.
Label: SYNTHETIC_HISTORICAL — not real-time sensor data.

Hazard pair: Extreme Cloudburst → Debris Flow + GLOF → Flash Flood
Region: Mandakini River valley, Kedarnath, Uttarakhand
"""
from datetime import datetime, timezone

# Real event: 16–17 June 2013, Kedarnath temple area
# ~5,700+ fatalities, one of India's worst recorded disasters
REAL_EVENT_TIMESTAMP = datetime(2013, 6, 16, 22, 0, 0, tzinfo=timezone.utc)  # ~03:30 AM IST 17 Jun

KEDARNATH_TERRAIN = {
    "slope_degrees": 38.0,
    "channel_width_m": 80.0,
    "valley_length_km": 24.0,
    "debris_volume_m3": 2_000_000,
    "upstream_lake_area_km2": 0.8,  # Chorabari glacier lake
}

KEDARNATH_IMPACT = {
    "population_exposed": 8_500,    # pilgrims + locals in valley
    "hospitals_exposed": 1,
    "roads_affected_km": 42,
    "shelters_available": 4,
}

KEDARNATH_FRAMES = [
    {
        "offset_hours": -72,
        "label": "T-72h: Normal monsoon conditions",
        "simulation_timestamp": "2013-06-13T22:00:00+00:00",
        "is_real_event": False,
        "notes": "Normal pre-monsoon activity. Kedarnath temple area receiving pilgrims.",
        "data_source": "SYNTHETIC_HISTORICAL",
        "inference": {
            "probability": 0.03,
            "time_lag_min_hours": 2.0,
            "time_lag_max_hours": 4.5,
            "tier": "GREEN",
            "causal_path": [
                {"node": "Rainfall", "label": "Rain (38mm/24h)", "probability": 0.07, "state": "LOW"},
                {"node": "SoilSaturation", "label": "Soil Sat (62%)", "probability": 0.62, "state": "MEDIUM"},
                {"node": "LandslideProbability", "label": "Debris Flow", "probability": 0.03, "state": "LOW"},
                {"node": "RiverBlockage", "label": "River Blockage", "probability": 0.02, "state": "LOW"},
                {"node": "DownstreamFlood", "label": "Flash Flood", "probability": 0.03, "state": "LOW"},
            ],
        },
        "impact": {**KEDARNATH_IMPACT, "impact_score": 1.4},
        "alert": {"tier": "GREEN", "recommended_action": "NORMAL: Routine monitoring. No cascade risk.", "probability": 0.03, "impact_score": 1.4},
    },
    {
        "offset_hours": -48,
        "label": "T-48h: Monsoon surge — IMD red alert for Uttarakhand",
        "simulation_timestamp": "2013-06-14T22:00:00+00:00",
        "is_real_event": False,
        "notes": "Monsoon trough intensifies. 125mm/24h recorded. Chorabari glacier lake filling.",
        "data_source": "SYNTHETIC_HISTORICAL",
        "inference": {
            "probability": 0.15,
            "time_lag_min_hours": 2.0,
            "time_lag_max_hours": 4.5,
            "tier": "YELLOW",
            "causal_path": [
                {"node": "Rainfall", "label": "Rain (125mm/24h)", "probability": 0.52, "state": "MEDIUM"},
                {"node": "SoilSaturation", "label": "Soil Sat (75%)", "probability": 0.75, "state": "HIGH"},
                {"node": "LandslideProbability", "label": "Debris Flow", "probability": 0.22, "state": "MEDIUM"},
                {"node": "RiverBlockage", "label": "River Blockage", "probability": 0.12, "state": "LOW"},
                {"node": "DownstreamFlood", "label": "Flash Flood", "probability": 0.15, "state": "LOW"},
            ],
        },
        "impact": {**KEDARNATH_IMPACT, "impact_score": 13.2},
        "alert": {"tier": "YELLOW", "recommended_action": "WATCH: Heavy rainfall event. Alert pilgrims in Kedarnath valley. Monitor Mandakini river gauge.", "probability": 0.15, "impact_score": 13.2},
    },
    {
        "offset_hours": -36,
        "label": "T-36h: Extreme precipitation — 175mm/24h",
        "simulation_timestamp": "2013-06-15T10:00:00+00:00",
        "is_real_event": False,
        "notes": "175mm/24h — Kedarnath slopes at saturation. Chorabari moraine under stress.",
        "data_source": "SYNTHETIC_HISTORICAL",
        "inference": {
            "probability": 0.32,
            "time_lag_min_hours": 2.0,
            "time_lag_max_hours": 4.5,
            "tier": "YELLOW",
            "causal_path": [
                {"node": "Rainfall", "label": "Rain (175mm/24h)", "probability": 0.78, "state": "HIGH"},
                {"node": "SoilSaturation", "label": "Soil Sat (86%)", "probability": 0.86, "state": "HIGH"},
                {"node": "LandslideProbability", "label": "Debris Flow", "probability": 0.45, "state": "MEDIUM"},
                {"node": "RiverBlockage", "label": "River Blockage", "probability": 0.28, "state": "MEDIUM"},
                {"node": "DownstreamFlood", "label": "Flash Flood", "probability": 0.32, "state": "MEDIUM"},
            ],
        },
        "impact": {**KEDARNATH_IMPACT, "impact_score": 27.8},
        "alert": {"tier": "YELLOW", "recommended_action": "WATCH: Extreme rainfall on saturated slopes. Strongly advise pilgrim evacuation from Kedarnath temple compound.", "probability": 0.32, "impact_score": 27.8},
    },
    {
        "offset_hours": -24,
        "label": "T-24h: ⚠ ORANGE — Cloudburst + glacier lake stress",
        "simulation_timestamp": "2013-06-15T22:00:00+00:00",
        "is_real_event": False,
        "notes": "220mm/24h — well above Caine threshold at 38° slope. Chorabari glacier lake moraine under critical stress. CascadeIQ raises ORANGE.",
        "data_source": "SYNTHETIC_HISTORICAL",
        "inference": {
            "probability": 0.52,
            "time_lag_min_hours": 2.0,
            "time_lag_max_hours": 4.5,
            "tier": "ORANGE",
            "causal_path": [
                {"node": "Rainfall", "label": "Rain (220mm/24h)", "probability": 0.91, "state": "HIGH"},
                {"node": "SoilSaturation", "label": "Soil Sat (91%)", "probability": 0.91, "state": "HIGH"},
                {"node": "LandslideProbability", "label": "Debris Flow", "probability": 0.65, "state": "HIGH"},
                {"node": "RiverBlockage", "label": "River Blockage", "probability": 0.48, "state": "MEDIUM"},
                {"node": "DownstreamFlood", "label": "Flash Flood", "probability": 0.52, "state": "MEDIUM"},
            ],
        },
        "impact": {**KEDARNATH_IMPACT, "impact_score": 44.6},
        "alert": {"tier": "ORANGE", "recommended_action": "ADVISORY: Immediate pilgrim evacuation order for Kedarnath — Sonprayag corridor. Close Kedarnath helicopter services. Alert SDRF Uttarakhand. Estimated flash flood arrival: 2–4.5 hours from blockage.", "probability": 0.52, "impact_score": 44.6},
    },
    {
        "offset_hours": -12,
        "label": "T-12h: 🚨 RED — Chorabari lake failure imminent",
        "simulation_timestamp": "2013-06-16T10:00:00+00:00",
        "is_real_event": False,
        "notes": "Chorabari glacier lake overtopping. Debris flows active on Mandakini slopes. RED alert raised 12 hours before main event.",
        "data_source": "SYNTHETIC_HISTORICAL",
        "inference": {
            "probability": 0.76,
            "time_lag_min_hours": 2.0,
            "time_lag_max_hours": 4.5,
            "tier": "RED",
            "causal_path": [
                {"node": "Rainfall", "label": "Rain (195mm/24h)", "probability": 0.87, "state": "HIGH"},
                {"node": "SoilSaturation", "label": "Soil Sat (95%)", "probability": 0.95, "state": "HIGH"},
                {"node": "LandslideProbability", "label": "Debris Flow", "probability": 0.82, "state": "HIGH"},
                {"node": "RiverBlockage", "label": "River Blockage", "probability": 0.70, "state": "HIGH"},
                {"node": "DownstreamFlood", "label": "Flash Flood", "probability": 0.76, "state": "HIGH"},
            ],
        },
        "impact": {**KEDARNATH_IMPACT, "impact_score": 71.2},
        "alert": {"tier": "RED", "recommended_action": "IMMEDIATE: Full evacuation of Kedarnath valley. All pilgrims to move to higher ground or Gaurikund. SDRF rescue teams deploy to Sonprayag. Flash flood arrival: 2–4.5 hours.", "probability": 0.76, "impact_score": 71.2},
    },
    {
        "offset_hours": 0,
        "label": "T=0: ⭐ CONFIRMED — Kedarnath cloudburst + GLOF, 16–17 Jun 2013",
        "simulation_timestamp": "2013-06-16T22:00:00+00:00",
        "is_real_event": True,
        "notes": "CONFIRMED REAL EVENT: Chorabari glacier lake burst + extreme cloudburst. ~5,700+ fatalities. One of India's deadliest recorded disasters. CascadeIQ had raised RED 12 hours earlier.",
        "data_source": "SYNTHETIC_HISTORICAL",
        "inference": {
            "probability": 0.94,
            "time_lag_min_hours": 0,
            "time_lag_max_hours": 2.5,
            "tier": "RED",
            "causal_path": [
                {"node": "Rainfall", "label": "Rain (210mm/24h)", "probability": 0.94, "state": "HIGH"},
                {"node": "SoilSaturation", "label": "Soil Sat (98%)", "probability": 0.98, "state": "HIGH"},
                {"node": "LandslideProbability", "label": "Debris Flow", "probability": 0.95, "state": "HIGH"},
                {"node": "RiverBlockage", "label": "River Blockage", "probability": 0.92, "state": "HIGH"},
                {"node": "DownstreamFlood", "label": "Flash Flood", "probability": 0.94, "state": "HIGH"},
            ],
        },
        "impact": {**KEDARNATH_IMPACT, "impact_score": 95.4},
        "alert": {"tier": "RED", "recommended_action": "EVENT CONFIRMED. Kedarnath valley devastated. Full emergency response. CascadeIQ had provided 12 hours of verified lead time.", "probability": 0.94, "impact_score": 95.4},
    },
]


def get_kedarnath_replay():
    """Return the Kedarnath 2013 replay data for the API."""
    return {
        "event_name": "kedarnath_2013",
        "region": "Kedarnath — Mandakini Valley",
        "real_event_timestamp": REAL_EVENT_TIMESTAMP.isoformat(),
        "terrain": KEDARNATH_TERRAIN,
        "data_source": "SYNTHETIC_HISTORICAL",
        "caution": "Synthetic reconstruction from published research (Dobhal et al. 2013). "
                   "Not real-time sensor data. All frames labeled SYNTHETIC_HISTORICAL.",
        "references": [
            "Dobhal, D.P. et al. (2013). Kedarnath disaster: facts and plausible causes.",
            "Zainuddin, K. et al. (2020). Hydrological assessment of Kedarnath disaster.",
        ],
        "frames": KEDARNATH_FRAMES,
    }
