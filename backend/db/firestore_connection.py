"""Verify Firestore access using Application Default Credentials."""

from google.cloud import firestore


def main() -> None:
    # Uses GOOGLE_CLOUD_PROJECT or the active gcloud project plus ADC.
    db = firestore.Client(database="auditly-db")
    doc_ref = db.collection("users").document("test-user")
    doc_ref.set(
        {
            "name": "Test",
            "status": "Connected via ADC",
        }
    )
    print("Connected and document written successfully!")


if __name__ == "__main__":
    main()
