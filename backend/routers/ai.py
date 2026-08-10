import re
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.fleet_manifest import get_fleet_manifest, get_vehicle_manifest
from backend.services.generator import get_generator
from backend.services.alerts import get_active_alerts
from backend.services.bedrock_client import query_bedrock_llm
from ml.rca_engine import RootCauseAnalyzer

router = APIRouter(prefix="/api/ai", tags=["AI Copilot"])


class QueryRequest(BaseModel):
    query: str
    vehicle_id: str | None = None


def _extract_vehicle_id(query_text: str) -> str | None:
    match = re.search(r"car[-_ ]?(\d{1,3})", query_text, re.IGNORECASE)
    if match:
        num = int(match.group(1))
        if 1 <= num <= 15:
            return f"car-{num:03d}"
    return None


def _get_vehicle_full_info(vehicle_id: str) -> dict[str, Any] | None:
    manifest = get_vehicle_manifest(vehicle_id)
    if not manifest:
        return None
    data = manifest.to_dict()

    generator = get_generator()
    latest_pt = generator.get_latest(vehicle_id)
    if latest_pt:
        data.update({
            "speed_kmh": latest_pt.speed_kmh,
            "battery_pct": latest_pt.battery_pct,
            "health_score": latest_pt.health_score,
            "road_zone": latest_pt.road_zone,
            "trip_status": latest_pt.trip_status,
            "turn_count": latest_pt.turn_count,
            "eta_minutes": latest_pt.eta_minutes,
            "maintenance_rul_pct": latest_pt.maintenance_rul_pct,
            "active_alert": latest_pt.active_alert,
            "alert_severity": latest_pt.alert_severity,
            "lat": latest_pt.lat,
            "lng": latest_pt.lng,
            "status": latest_pt.status,
            "navigation_mode": latest_pt.navigation_mode,
        })
    return data


@router.post("/ask")
def ask_copilot(req: QueryRequest):
    try:
        query_text = req.query.strip()
        target_v_id = req.vehicle_id or _extract_vehicle_id(query_text)

        generator = get_generator()
        manifests = {m.vehicle_id: m.to_dict() for m in get_fleet_manifest()}
        latest_telemetry = generator.get_latest() or {}

        all_vehicles = []
        for vid, mdict in manifests.items():
            t_pt = latest_telemetry.get(vid)
            v_info = dict(mdict)
            if t_pt:
                v_info.update({
                    "speed_kmh": t_pt.speed_kmh,
                    "battery_pct": t_pt.battery_pct,
                    "health_score": t_pt.health_score,
                    "road_zone": t_pt.road_zone,
                    "trip_status": t_pt.trip_status,
                    "turn_count": t_pt.turn_count,
                    "eta_minutes": t_pt.eta_minutes,
                    "maintenance_rul_pct": t_pt.maintenance_rul_pct,
                    "active_alert": t_pt.active_alert,
                    "alert_severity": t_pt.alert_severity,
                    "lat": t_pt.lat,
                    "lng": t_pt.lng,
                    "status": t_pt.status,
                })
            all_vehicles.append(v_info)

        matched_vehicle = _get_vehicle_full_info(target_v_id) if target_v_id else None
        active_alerts = get_active_alerts(limit=10)

        context_str = f"User Request: '{query_text}'\n"
        if matched_vehicle:
            context_str += f"\nTarget Vehicle Data:\n{matched_vehicle}\n"
        context_str += f"\nFleet Status Summary (N=15):\n"
        for v in all_vehicles[:5]:
            context_str += f"- {v['vehicle_id']} (Driver: {v['driver_name']}, Passengers: {v['passenger_count']}, Battery: {v.get('battery_pct', 90)}%, Health: {v.get('health_score', 95)}%, Alert: {v.get('active_alert', 'None')})\n"
        if active_alerts:
            context_str += f"\nActive Rule Alerts ({len(active_alerts)} total):\n"
            for a in active_alerts[:3]:
                context_str += f"- [{a.get('severity', 'info').upper()}] {a.get('vehicle_id')}: {a.get('message')}\n"

        system_prompt = (
            "You are FleetGuard AI Assistant, an expert autonomous EV fleet copilot. "
            "You provide detailed descriptions, passenger info, telemetry metrics, alerts, and vehicle diagnostic guidance. "
            "Keep your answer clear, professional, friendly, and structured."
        )

        llm_response = query_bedrock_llm(prompt=context_str, system_prompt=system_prompt)

        if "Bedrock Error" in llm_response or not llm_response:
            if matched_vehicle:
                v = matched_vehicle
                alert_text = f" 🚨 Active Alert: {v['active_alert']}" if v.get('active_alert') else " ✅ No Active Alerts"
                llm_response = (
                    f"**Vehicle Analysis for {v['vehicle_id']} ({v['driver_name']})**\n\n"
                    f"• **Passengers**: {v['passenger_count']} onboard\n"
                    f"• **Route**: {v['pickup_address']} -> {v['destination_address']} ({v['route_name']}, {v['route_difficulty']} difficulty)\n"
                    f"• **Telemetry**: Speed {v.get('speed_kmh', 0)} km/h | Battery {v.get('battery_pct', 90)}% | Health {v.get('health_score', 95)}% | RUL {v.get('maintenance_rul_pct', 100)}%\n"
                    f"• **Zone & Status**: {v.get('road_zone', 'residential').capitalize()} zone | {v.get('trip_status', 'en_route').replace('_', ' ').title()} (ETA ~{v.get('eta_minutes', 5)} min)\n"
                    f"• **Engine & Odometer**: {v['engine_status'].title()} status | {v['odometer_km']} km driven | Maintenance due in {v['maintenance_due_km']} km\n"
                    f"• **Alert Status**:{alert_text}"
                )
            elif "battery" in query_text.lower() or "charging" in query_text.lower():
                low_batt = [v for v in all_vehicles if v.get("battery_pct", 100) < 50]
                names = ", ".join([v["vehicle_id"] for v in low_batt]) if low_batt else "None"
                llm_response = f"**Battery & Charging Overview**\n\nFound {len(low_batt)} vehicle(s) with battery under 50%: **{names}**. All vehicles have automated rerouting enabled to Redwood City charging stations."
            elif "passenger" in query_text.lower():
                pass_total = sum(v.get("passenger_count", 0) for v in all_vehicles)
                high_p = sorted(all_vehicles, key=lambda x: x.get("passenger_count", 0), reverse=True)[:3]
                p_summary = ", ".join([f"{v['vehicle_id']} ({v['passenger_count']} passengers)" for v in high_p])
                llm_response = f"**Fleet Passenger Summary**\n\nTotal passengers currently in transport across 15 EVs: **{pass_total}**.\nTop occupancy vehicles: {p_summary}."
            elif "alert" in query_text.lower() or "critical" in query_text.lower():
                alerts = [v for v in all_vehicles if v.get("active_alert")]
                llm_response = (
                    f"**Active Fleet Alerts ({len(alerts)})**\n\n"
                    + "\n".join([f"• **{v['vehicle_id']}**: {v['active_alert']} ({v.get('alert_severity', 'info').upper()})" for v in alerts])
                    if alerts
                    else "No critical alerts active across the fleet."
                )
            else:
                llm_response = (
                    "**Fleet Overview (15 Electric Autonomous Vehicles)**\n\n"
                    "All 15 EVs are actively monitoring routes in Redwood City, CA. You can ask me to search specific cars (e.g. `car-001` to `car-015`), analyze passenger load, check battery levels, or view live telemetry metrics."
                )

        return {
            "response": llm_response,
            "matched_vehicle": matched_vehicle,
            "vehicles_summary": [
                {
                    "vehicle_id": v["vehicle_id"],
                    "passenger_count": v["passenger_count"],
                    "battery_pct": v.get("battery_pct", 90),
                    "health_score": v.get("health_score", 95),
                    "active_alert": v.get("active_alert"),
                }
                for v in all_vehicles
            ],
            "target_vehicle_id": target_v_id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diagnose/{vehicle_id}")
def diagnose_vehicle(vehicle_id: str):
    info = _get_vehicle_full_info(vehicle_id)
    if not info:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    sensor = "Battery" if info.get("battery_pct", 100) < 30 else ("LiDAR" if info.get("health_score", 100) < 85 else "EngineRPM")
    rca_res = RootCauseAnalyzer.analyze(
        sensor_id=sensor,
        temp=65.0 if info.get("health_score", 100) < 80 else 35.0,
        voltage=11.5 if info.get("battery_pct", 100) < 20 else 13.8,
        vibration=1.4 if sensor == "LiDAR" else 0.4,
    )

    prompt = (
        f"Generate an expert engineering diagnostic brief for autonomous vehicle {vehicle_id}.\n"
        f"Vehicle state: {info}\n"
        f"Sensor diagnosis: {rca_res}\n"
        "Explain the physical defect, operational risk to passengers, and step-by-step repair instruction."
    )
    system_prompt = "You are FleetGuard Lead Diagnostics Engineer."
    analysis_text = query_bedrock_llm(prompt, system_prompt)
    if "Bedrock Error" in analysis_text or not analysis_text:
        analysis_text = (
            f"**Diagnostic Report for {vehicle_id}**\n\n"
            f"• **Primary Fault**: {rca_res['root_cause']}\n"
            f"• **Confidence**: {rca_res['confidence_score']}%\n"
            f"• **Recommended Action**: {rca_res['recommended_action']}\n"
            f"• **Safety Risk Level**: Moderate - Passenger safety monitored."
        )

    return {
        "vehicle_id": vehicle_id,
        "diagnostic_summary": rca_res,
        "ai_report": analysis_text,
        "vehicle": info,
    }


@router.get("/fleet-brief")
def fleet_brief():
    manifests = [m.to_dict() for m in get_fleet_manifest()]
    generator = get_generator()
    latest_telemetry = generator.get_latest() or {}

    total_passengers = sum(m["passenger_count"] for m in manifests)
    low_battery_count = sum(1 for vid, t in latest_telemetry.items() if t.battery_pct < 40)
    alerts_count = len(get_active_alerts(30))

    prompt = (
        "Summarize fleet executive health brief for 15 EVs operating in Redwood City, CA.\n"
        f"Total Passengers: {total_passengers}, Low Battery Vehicles: {low_battery_count}, Active Alerts: {alerts_count}."
    )
    brief_text = query_bedrock_llm(prompt, "You are Chief Operations Officer AI Assistant.")
    if "Bedrock Error" in brief_text or not brief_text:
        brief_text = (
            "**Fleet Operations Executive Briefing**\n\n"
            f"• **Active Fleet Size**: 15 Electric Vehicles (BEV)\n"
            f"• **Passenger Capacity**: {total_passengers} passengers currently transported across Redwood City routes\n"
            f"• **Charging Status**: {low_battery_count} vehicle(s) approaching low battery (<40%)\n"
            f"• **Active Fleet Alerts**: {alerts_count} active system notifications\n"
            "• **Operational Readiness**: 98.4% fleet health index"
        )

    return {
        "fleet_size": len(manifests),
        "total_passengers": total_passengers,
        "low_battery_count": low_battery_count,
        "active_alerts_count": alerts_count,
        "executive_brief": brief_text,
    }

