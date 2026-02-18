"""Seed database with sample predicate devices and test data."""
import asyncio
from datetime import datetime
from app.core.database import SessionLocal
from app.models.submission import PredicateDevice


def seed_predicate_devices():
    """Seed sample predicate devices."""
    db = SessionLocal()

    sample_devices = [
        {
            "k_number": "K123456",
            "device_name": "HeartWatch 3000",
            "manufacturer": "CardioTech Inc",
            "device_class": "II",
            "product_code": "DXH",
            "indications_for_use": "Continuous cardiac monitoring for patients at risk of arrhythmias",
            "technological_characteristics": {
                "sensing_method": "Electrocardiogram (ECG)",
                "electrodes": "3-lead configuration",
                "power": "Rechargeable lithium-ion battery",
                "connectivity": "Bluetooth 5.0",
                "memory": "48 hours continuous recording"
            },
            "performance_data": {
                "sensitivity": "99.2%",
                "specificity": "98.7%",
                "accuracy": "99.0%",
                "battery_life": "7 days typical use"
            },
            "decision": "Substantially Equivalent",
            "decision_date": datetime(2022, 6, 15)
        },
        {
            "k_number": "K789012",
            "device_name": "BloodFlow Analyzer",
            "manufacturer": "VascuMed Corporation",
            "device_class": "II",
            "product_code": "DQN",
            "indications_for_use": "Non-invasive measurement of blood flow velocity in peripheral arteries",
            "technological_characteristics": {
                "technology": "Doppler ultrasound",
                "frequency": "8 MHz",
                "probe_type": "Pencil probe",
                "display": "7-inch color LCD",
                "measurements": "Peak velocity, mean velocity, resistance index"
            },
            "performance_data": {
                "accuracy": "±5% of reading",
                "resolution": "1 cm/s",
                "depth_penetration": "5 cm",
                "measurement_range": "0-400 cm/s"
            },
            "decision": "Substantially Equivalent",
            "decision_date": datetime(2021, 11, 3)
        },
        {
            "k_number": "K345678",
            "device_name": "GlucoseGuard Pro",
            "manufacturer": "DiabetesTech Solutions",
            "device_class": "II",
            "product_code": "NBW",
            "indications_for_use": "Continuous glucose monitoring for diabetes management",
            "technological_characteristics": {
                "sensor_type": "Electrochemical glucose oxidase",
                "calibration": "Factory calibrated, no fingerstick required",
                "wear_time": "14 days",
                "connectivity": "NFC and Bluetooth",
                "alerts": "Customizable high/low glucose alerts"
            },
            "performance_data": {
                "mard": "9.3%",  # Mean Absolute Relative Difference
                "range": "40-400 mg/dL",
                "lag_time": "2.5 minutes",
                "clinical_accuracy": "99.1% in hypoglycemia range"
            },
            "decision": "Substantially Equivalent",
            "decision_date": datetime(2023, 2, 20)
        },
        {
            "k_number": "K901234",
            "device_name": "RespiMonitor Elite",
            "manufacturer": "PulmoTech International",
            "device_class": "II",
            "product_code": "BZX",
            "indications_for_use": "Home monitoring of respiratory rate and oxygen saturation",
            "technological_characteristics": {
                "sensors": "Pulse oximetry and impedance pneumography",
                "form_factor": "Wearable chest patch",
                "size": "5cm x 5cm x 1cm",
                "weight": "30 grams",
                "connectivity": "WiFi and cellular (LTE-M)"
            },
            "performance_data": {
                "spo2_accuracy": "±2% (70-100% range)",
                "respiratory_rate_accuracy": "±2 breaths/min",
                "battery_life": "10 days continuous use",
                "water_resistance": "IP67 rated"
            },
            "decision": "Substantially Equivalent",
            "decision_date": datetime(2022, 9, 8)
        },
        {
            "k_number": "K567890",
            "device_name": "NeuroStim Therapy System",
            "manufacturer": "NeuroCare Devices",
            "device_class": "III",
            "product_code": "GZB",
            "indications_for_use": "Transcranial magnetic stimulation for treatment-resistant depression",
            "technological_characteristics": {
                "stimulation_type": "Repetitive TMS (rTMS)",
                "coil_design": "Figure-8 coil",
                "frequency_range": "1-50 Hz",
                "intensity_control": "0-100% motor threshold",
                "navigation": "Neuronavigation system with MRI integration"
            },
            "performance_data": {
                "treatment_sessions": "20-30 sessions typical course",
                "session_duration": "30-40 minutes",
                "response_rate": "58% improvement in depression scores",
                "safety_profile": "0.1% seizure risk"
            },
            "decision": "Substantially Equivalent",
            "decision_date": datetime(2023, 5, 12)
        }
    ]

    for device_data in sample_devices:
        # Check if device already exists
        existing = db.query(PredicateDevice).filter(
            PredicateDevice.k_number == device_data["k_number"]
        ).first()

        if not existing:
            device = PredicateDevice(**device_data)
            db.add(device)
            print(f"Added predicate device: {device_data['device_name']} ({device_data['k_number']})")
        else:
            print(f"Device {device_data['k_number']} already exists, skipping...")

    db.commit()
    db.close()
    print("\n✅ Predicate device seeding complete!")


if __name__ == "__main__":
    print("Seeding predicate devices...")
    seed_predicate_devices()
