import pytest


@pytest.mark.asyncio
async def test_company_crud_and_deduplication(async_client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create company
    create_payload = {
        "name": "Gamma Technologies",
        "target_url": "https://gammatech.example.com/about",
        "industry": "Artificial Intelligence",
        "description": "Next-gen AI solutions",
    }
    res = await async_client.post("/api/v1/companies", json=create_payload, headers=headers)
    assert res.status_code == 200
    company_data = res.json()
    assert company_data["primary_domain"] == "gammatech.example.com"
    company_id = company_data["id"]

    # 2. Duplicate insertion test: seeding same domain should return existing company
    dup_payload = {
        "target_url": "http://gammatech.example.com",
    }
    dup_res = await async_client.post("/api/v1/companies", json=dup_payload, headers=headers)
    assert dup_res.status_code == 200
    assert dup_res.json()["id"] == company_id

    # 3. Get Company Details
    detail_res = await async_client.get(f"/api/v1/companies/{company_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["name"] == "Gamma Technologies"

    # 4. Update Company
    update_res = await async_client.put(
        f"/api/v1/companies/{company_id}",
        json={"status": "QUALIFIED", "headquarters": "Austin, TX"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "QUALIFIED"

    # 5. List with filter
    list_res = await async_client.get("/api/v1/companies?status=QUALIFIED", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert any(c["id"] == company_id for c in items)

    # 6. Delete Company
    del_res = await async_client.delete(f"/api/v1/companies/{company_id}", headers=headers)
    assert del_res.status_code == 200
