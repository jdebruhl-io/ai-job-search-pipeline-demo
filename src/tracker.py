import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from config import TRACKER_FILE


def load_applications():
    if not os.path.exists(TRACKER_FILE):
        return []
    with open(TRACKER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_applications(apps):
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(apps, f, indent=2, ensure_ascii=False)


def add_application():
    print("\n--- ADD APPLICATION ---")
    app = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "company": input("Company name: ").strip(),
        "title": input("Job title: ").strip(),
        "url": input("Job URL (or press Enter to skip): ").strip(),
        "source": input("Where found (RemoteOK/Jobicy/Direct/LinkedIn etc): ").strip(),
        "date_applied": input("Date applied (YYYY-MM-DD or press Enter for today): ").strip() or datetime.now().strftime("%Y-%m-%d"),
        "resume_version": input("Resume version used (e.g. WWT_tailored / master): ").strip(),
        "cover_letter": input("Cover letter sent? (y/n): ").strip().lower() == "y",
        "status": "Applied",
        "notes": input("Any notes: ").strip(),
        "follow_up_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "history": [
            {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "event": "Application submitted"
            }
        ]
    }

    apps = load_applications()
    apps.append(app)
    save_applications(apps)
    print(f"\n✓ Added: {app['title']} @ {app['company']}")
    print(f"  Follow-up reminder: {app['follow_up_date']}")


def update_status():
    apps = load_applications()
    if not apps:
        print("No applications tracked yet.")
        return

    print("\n--- UPDATE STATUS ---")
    list_applications(apps)

    try:
        idx = int(input("\nEnter application number to update: ")) - 1
        if idx < 0 or idx >= len(apps):
            print("Invalid number.")
            return
    except ValueError:
        print("Invalid input.")
        return

    app = apps[idx]
    print(f"\nUpdating: {app['title']} @ {app['company']}")
    print(f"Current status: {app['status']}")
    print("\nStatus options:")
    statuses = [
        "Applied",
        "Phone Screen Scheduled",
        "Phone Screen Complete",
        "Technical Interview Scheduled",
        "Technical Interview Complete",
        "Final Interview Scheduled",
        "Final Interview Complete",
        "Offer Received",
        "Offer Accepted",
        "Offer Declined",
        "Rejected",
        "Withdrawn",
        "No Response - Following Up"
    ]

    for i, s in enumerate(statuses):
        print(f"  {i+1}. {s}")

    try:
        status_idx = int(input("\nSelect status number: ")) - 1
        new_status = statuses[status_idx]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    notes = input("Add notes (or press Enter to skip): ").strip()

    app["status"] = new_status
    app["history"].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "event": new_status,
        "notes": notes
    })

    # Auto-set follow-up dates based on status
    if "Scheduled" in new_status:
        interview_date = input("Interview date (YYYY-MM-DD): ").strip()
        app["interview_date"] = interview_date
        app["follow_up_date"] = interview_date
    elif "Complete" in new_status:
        app["follow_up_date"] = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    elif new_status == "Offer Received":
        app["follow_up_date"] = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

    if notes:
        app["notes"] = notes

    save_applications(apps)
    print(f"\n✓ Updated: {new_status}")


def list_applications(apps=None):
    if apps is None:
        apps = load_applications()

    if not apps:
        print("No applications tracked yet.")
        return

    today = datetime.now().strftime("%Y-%m-%d")

    print("\n--- YOUR APPLICATIONS ---")
    print(f"{'#':<4} {'Company':<30} {'Title':<40} {'Status':<30} {'Follow-up':<12} {'!':<3}")
    print("-" * 125)

    for i, app in enumerate(apps):
        follow_up = app.get("follow_up_date", "")
        overdue = "⚠" if follow_up and follow_up <= today and app["status"] not in [
            "Offer Accepted", "Offer Declined", "Rejected", "Withdrawn"
        ] else ""

        print(f"{i+1:<4} {app['company'][:28]:<30} {app['title'][:38]:<40} "
              f"{app['status'][:28]:<30} {follow_up:<12} {overdue:<3}")


def show_followups():
    apps = load_applications()
    today = datetime.now().strftime("%Y-%m-%d")
    upcoming = datetime.now() + timedelta(days=3)
    upcoming_str = upcoming.strftime("%Y-%m-%d")

    due = [a for a in apps if
           a.get("follow_up_date", "9999") <= upcoming_str and
           a["status"] not in ["Offer Accepted", "Offer Declined", "Rejected", "Withdrawn"]]

    if not due:
        print("\nNo follow-ups due in the next 3 days.")
        return

    print(f"\n--- FOLLOW-UPS DUE (next 3 days) ---")
    for app in due:
        overdue = " ⚠ OVERDUE" if app.get("follow_up_date", "") <= today else ""
        print(f"\n{app['company']} — {app['title']}")
        print(f"  Status: {app['status']}")
        print(f"  Follow-up: {app['follow_up_date']}{overdue}")
        print(f"  Notes: {app.get('notes', 'None')}")


def show_history():
    apps = load_applications()
    if not apps:
        print("No applications tracked yet.")
        return

    list_applications(apps)
    try:
        idx = int(input("\nEnter application number to view history: ")) - 1
        app = apps[idx]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    print(f"\n--- HISTORY: {app['title']} @ {app['company']} ---")
    for event in app.get("history", []):
        print(f"  {event['date']} — {event['event']}")
        if event.get("notes"):
            print(f"    Notes: {event['notes']}")


def main_menu():
    while True:
        print("\n" + "=" * 40)
        print("  APPLICATION TRACKER")
        print("=" * 40)
        print("  1. Add new application")
        print("  2. Update application status")
        print("  3. View all applications")
        print("  4. View follow-ups due")
        print("  5. View application history")
        print("  6. Exit")
        print("=" * 40)

        choice = input("Select option: ").strip()

        if choice == "1":
            add_application()
        elif choice == "2":
            update_status()
        elif choice == "3":
            list_applications()
        elif choice == "4":
            show_followups()
        elif choice == "5":
            show_history()
        elif choice == "6":
            break
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main_menu()

