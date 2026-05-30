import os
import pandas as pd

os.makedirs("data", exist_ok=True)

cases = [
    {
        "product_id": "risk_001",
        "title": "Whitening Anti-aging Face Cream 100% Effective",
        "description": "Remove wrinkles in 3 days. Guaranteed result for all skin types.",
        "brand": "GlowMax",
        "category": "Beauty",
        "manual_risk_level": "Medium",
        "manual_risk_types": "Misleading Claim; Beauty Claim Risk",
        "matched_rule_ids": "R001; R010",
        "label_notes": "Contains absolute efficacy claims and cosmetic overclaim."
    },
    {
        "product_id": "risk_002",
        "title": "Replica Luxury Designer Bag AAA Quality",
        "description": "Same as original designer bag with premium leather look.",
        "brand": "Unknown",
        "category": "Fashion",
        "manual_risk_level": "High",
        "manual_risk_types": "IP or Counterfeit Risk",
        "matched_rule_ids": "R005; R018",
        "label_notes": "Replica and same as original indicate counterfeit risk."
    },
    {
        "product_id": "risk_003",
        "title": "Hidden Spy Camera USB Charger",
        "description": "Secret recording device for home and office monitoring.",
        "brand": "CamPro",
        "category": "Electronics",
        "manual_risk_level": "High",
        "manual_risk_types": "Privacy and Safety Risk",
        "matched_rule_ids": "R013",
        "label_notes": "Hidden camera and secret recording imply privacy risk."
    },
    {
        "product_id": "risk_004",
        "title": "Herbal Capsules Cure Diabetes Naturally",
        "description": "Treat diabetes and reduce blood sugar permanently without medicine.",
        "brand": "HerbalLifePlus",
        "category": "Health",
        "manual_risk_level": "High",
        "manual_risk_types": "Medical or Health Claim; Restricted Product",
        "matched_rule_ids": "R002; R003",
        "label_notes": "Claims to cure and treat disease."
    },
    {
        "product_id": "risk_005",
        "title": "Tactical Knife Outdoor Survival Tool",
        "description": "Sharp combat-style knife for outdoor protection.",
        "brand": "SurvivalPro",
        "category": "Sports",
        "manual_risk_level": "High",
        "manual_risk_types": "Prohibited Product",
        "matched_rule_ids": "R004",
        "label_notes": "Weapon-related product."
    },
    {
        "product_id": "risk_006",
        "title": "Best Seller Hot Sale Cheap Shoes Free Shipping",
        "description": "Limited stock, buy now, best price today only.",
        "brand": "UrbanStep",
        "category": "Fashion",
        "manual_risk_level": "Medium",
        "manual_risk_types": "Listing Quality Issue; Misleading Promotion",
        "matched_rule_ids": "R007; R008",
        "label_notes": "Promotional title and fake urgency."
    },
    {
        "product_id": "risk_007",
        "title": "FDA Approved Slimming Tea Guaranteed Weight Loss",
        "description": "Lose weight instantly with clinically proven results.",
        "brand": "SlimFit",
        "category": "Health",
        "manual_risk_level": "Medium",
        "manual_risk_types": "Unverified Certification; Misleading Claim",
        "matched_rule_ids": "R001; R011",
        "label_notes": "Unverified certification and guaranteed claim."
    },
    {
        "product_id": "risk_008",
        "title": "Luxury Designer Watch Very Cheap Factory Direct",
        "description": "Premium official style watch at extremely low price.",
        "brand": "LuxTime",
        "category": "Accessories",
        "manual_risk_level": "Medium",
        "manual_risk_types": "Fraud or Quality Risk",
        "matched_rule_ids": "R018",
        "label_notes": "Luxury positioning with very cheap price indicates suspicious quality or authenticity."
    },
    {
        "product_id": "risk_009",
        "title": "No Brand Phone Cable",
        "description": "N/A",
        "brand": "Unknown",
        "category": "Electronics",
        "manual_risk_level": "Low",
        "manual_risk_types": "Listing Quality Issue",
        "matched_rule_ids": "R006; R015",
        "label_notes": "Missing description and unclear brand."
    },
    {
        "product_id": "risk_010",
        "title": "Guaranteed Next Day Worldwide Delivery Gift Box",
        "description": "Instant delivery worldwide in 24 hours for every country.",
        "brand": "GiftNow",
        "category": "Gifts",
        "manual_risk_level": "Medium",
        "manual_risk_types": "Service Claim Risk",
        "matched_rule_ids": "R020",
        "label_notes": "Unverifiable logistics claim."
    },
    {
        "product_id": "risk_011",
        "title": "Official Pokemon Anime Character Hoodie",
        "description": "Licensed character style hoodie with official logo.",
        "brand": "FanWear",
        "category": "Apparel",
        "manual_risk_level": "Medium",
        "manual_risk_types": "IP Risk",
        "matched_rule_ids": "R017",
        "label_notes": "Potential unauthorized character or logo use."
    },
    {
        "product_id": "risk_012",
        "title": "Toxic Industrial Cleaning Chemical",
        "description": "Highly corrosive liquid for heavy-duty use.",
        "brand": "CleanMax",
        "category": "Home Improvement",
        "manual_risk_level": "High",
        "manual_risk_types": "Hazardous Product",
        "matched_rule_ids": "R014",
        "label_notes": "Toxic and corrosive chemical."
    },
    {
        "product_id": "risk_013",
        "title": "Make Money Fast E-book Guaranteed Profit",
        "description": "Risk-free income method with guaranteed investment return.",
        "brand": "WealthGuide",
        "category": "Books",
        "manual_risk_level": "High",
        "manual_risk_types": "Financial Claim Risk",
        "matched_rule_ids": "R016",
        "label_notes": "Guaranteed profit and risk-free income claim."
    },
    {
        "product_id": "risk_014",
        "title": "Women Cotton T-shirt",
        "description": "Soft cotton crew neck T-shirt for daily wear.",
        "brand": "BasicWear",
        "category": "Apparel",
        "manual_risk_level": "Low",
        "manual_risk_types": "Normal Listing",
        "matched_rule_ids": "",
        "label_notes": "Normal product information."
    },
    {
        "product_id": "risk_015",
        "title": "Stainless Steel Water Bottle",
        "description": "Reusable 500ml stainless steel bottle for outdoor and office use.",
        "brand": "HydroDaily",
        "category": "Home",
        "manual_risk_level": "Low",
        "manual_risk_types": "Normal Listing",
        "matched_rule_ids": "",
        "label_notes": "Normal product information."
    },
    {
        "product_id": "risk_016",
        "title": "Random Text !!! Cheap Cheap Cheap",
        "description": "%%%% best best best ??? random text",
        "brand": "Unknown",
        "category": "Misc",
        "manual_risk_level": "Low",
        "manual_risk_types": "Listing Quality Issue",
        "matched_rule_ids": "R019",
        "label_notes": "Poor readability and broken description."
    },
    {
        "product_id": "risk_017",
        "title": "Antibiotic Cream Prescription Strength",
        "description": "Strong antibiotic treatment for skin infection.",
        "brand": "MediCare",
        "category": "Health",
        "manual_risk_level": "High",
        "manual_risk_types": "Restricted Product; Medical or Health Claim",
        "matched_rule_ids": "R002; R003",
        "label_notes": "Prescription and antibiotic treatment claim."
    },
    {
        "product_id": "risk_018",
        "title": "Adult Explicit Novelty Product",
        "description": "Erotic adult product for private use.",
        "brand": "PrivateLife",
        "category": "Adult",
        "manual_risk_level": "High",
        "manual_risk_types": "Sensitive Product",
        "matched_rule_ids": "R012",
        "label_notes": "Adult or explicit product."
    },
    {
        "product_id": "risk_019",
        "title": "CE Certified Baby Safety Seat",
        "description": "Official certified product, no documents provided.",
        "brand": "BabySafe",
        "category": "Baby",
        "manual_risk_level": "Medium",
        "manual_risk_types": "Unverified Certification",
        "matched_rule_ids": "R011",
        "label_notes": "Certification claim may need verification."
    },
    {
        "product_id": "risk_020",
        "title": "Generic Phone Case",
        "description": "Silicone phone case compatible with common smartphone models.",
        "brand": "Generic",
        "category": "Accessories",
        "manual_risk_level": "Low",
        "manual_risk_types": "Normal Listing",
        "matched_rule_ids": "",
        "label_notes": "Normal listing with clear product function."
    }
]

df = pd.DataFrame(cases)
output_path = "data/risky_test_cases.csv"
df.to_csv(output_path, index=False, encoding="utf-8-sig")

print("Saved:", output_path)
print("Rows:", len(df))
print(df.head())