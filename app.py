import re

import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder

DATASET_PATH = "Crop and fertilizer dataset.csv"


@st.cache_resource
def load_model():
    dataset = pd.read_csv(DATASET_PATH)
    encoder = OneHotEncoder(handle_unknown="ignore")
    X_encoded = encoder.fit_transform(dataset[["District_Name", "Soil_color"]])
    X_train, _, y_train, _ = train_test_split(
        X_encoded, dataset["Crop"], test_size=0.2, random_state=42
    )
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    return dataset, encoder, model


def extract_youtube_id(url):
    regex = (
        r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\s*[^\/\n\s]+\/|"
        r"(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    )
    match = re.search(regex, url)
    return match.group(1) if match else None


def get_recommendation(
    dataset, encoder, model, district, soil_color, nitrogen, phosphorus, potassium, ph, rainfall, temperature
):
    input_data = pd.DataFrame(
        [[nitrogen, phosphorus, potassium, ph, rainfall, temperature, district, soil_color]],
        columns=[
            "Nitrogen",
            "Phosphorus",
            "Potassium",
            "pH",
            "Rainfall",
            "Temperature",
            "District_Name",
            "Soil_color",
        ],
    )
    input_encoded = encoder.transform(input_data[["District_Name", "Soil_color"]])
    predicted_crop = model.predict(input_encoded)[0]

    crop_data = dataset[dataset["Crop"] == predicted_crop]
    if crop_data.empty:
        return None

    recommended_fertilizer = crop_data["Fertilizer"].values[0]
    link_data = dataset[
        (dataset["Crop"] == predicted_crop) & (dataset["Fertilizer"] == recommended_fertilizer)
    ]
    if link_data.empty:
        link = crop_data["Link"].values[0] if len(crop_data["Link"].values) > 0 else ""
    else:
        link = link_data["Link"].values[0]

    return {
        "predicted_crop": predicted_crop,
        "recommended_fertilizer": recommended_fertilizer,
        "link": link,
    }


def main():
    st.set_page_config(
        page_title="Crop Recommendation System",
        page_icon="🌾",
        layout="centered",
    )

    st.title("Crop Recommendation System")
    st.caption("Enter soil and climate details to get crop and fertilizer recommendations.")

    dataset, encoder, model = load_model()

    with st.form("recommendation_form"):
        col1, col2 = st.columns(2)
        with col1:
            district = st.selectbox(
                "District",
                sorted(dataset["District_Name"].dropna().unique()),
            )
            soil_color = st.selectbox(
                "Soil Color",
                sorted(dataset["Soil_color"].dropna().unique()),
            )
            nitrogen = st.selectbox(
                "Nitrogen (kg/ha)",
                sorted(dataset["Nitrogen"].dropna().unique()),
            )
            phosphorus = st.selectbox(
                "Phosphorus (kg/ha)",
                sorted(dataset["Phosphorus"].dropna().unique()),
            )
        with col2:
            potassium = st.selectbox(
                "Potassium (kg/ha)",
                sorted(dataset["Potassium"].dropna().unique()),
            )
            ph = st.selectbox("pH Level", sorted(dataset["pH"].dropna().unique()))
            rainfall = st.selectbox(
                "Rainfall (mm)",
                sorted(dataset["Rainfall"].dropna().unique()),
            )
            temperature = st.selectbox(
                "Temperature (°C)",
                sorted(dataset["Temperature"].dropna().unique()),
            )

        submitted = st.form_submit_button(
            "Recommend Crop",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        try:
            results = get_recommendation(
                dataset,
                encoder,
                model,
                district,
                soil_color,
                nitrogen,
                phosphorus,
                potassium,
                ph,
                rainfall,
                temperature,
            )
        except Exception as exc:
            st.error(f"Something went wrong: {exc}")
            return

        if not results:
            st.warning("No recommendation found for those inputs. Try different values.")
            return

        st.divider()
        st.subheader("Recommendation")
        st.metric("Recommended Crop", results["predicted_crop"])
        st.metric("Recommended Fertilizer", results["recommended_fertilizer"])

        if results["link"]:
            st.markdown(f"**More information:** [{results['link']}]({results['link']})")
            youtube_id = extract_youtube_id(results["link"])
            if youtube_id:
                st.markdown("**Related video**")
                st.components.v1.iframe(
                    f"https://www.youtube.com/embed/{youtube_id}",
                    height=400,
                )

    st.divider()
    st.caption("© Crop Recommendation System")


if __name__ == "__main__":
    main()
