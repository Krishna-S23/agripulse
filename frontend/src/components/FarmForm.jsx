import { useState } from "react";

const DISTRICTS = ["Coimbatore", "Erode", "Salem"];
const CROPS = ["Tomato", "Onion"];
const STAGES = [
  "Nursery",
  "Vegetative",
  "Flowering",
  "Fruiting",
  "Bulb Formation",
  "Maturation",
  "Harvest",
];
const SOIL_TYPES = [
  "Red Loam",
  "Black Soil",
  "Sandy Loam",
  "Clay Loam",
  "Laterite",
  "Alluvial",
];

export default function FarmForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    district: "Coimbatore",
    location: "",
    crop: "Tomato",
    area_acres: "",
    growth_stage: "Flowering",
    soil_type: "Red Loam",
  });

  const update = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      ...form,
      area_acres: form.area_acres ? parseFloat(form.area_acres) : null,
    });
  };

  return (
    <form className="ledger" onSubmit={handleSubmit}>
      <div className="ledger-grid">
        <div className="field">
          <label htmlFor="district">District</label>
          <select
            id="district"
            value={form.district}
            onChange={update("district")}
          >
            {DISTRICTS.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>
        {/* <div className="field">
          <label htmlFor="location">Location / Taluk</label>
          <input id="location" value={form.location} onChange={update('location')} placeholder="e.g. Sulur" />
        </div> */}
        <div className="field">
          <label htmlFor="crop">Crop</label>
          <select id="crop" value={form.crop} onChange={update("crop")}>
            {CROPS.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="stage">Growth stage</label>
          <select
            id="stage"
            value={form.growth_stage}
            onChange={update("growth_stage")}
          >
            {STAGES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="area">Area (acres)</label>
          <input
            id="area"
            type="number"
            step="0.1"
            value={form.area_acres}
            onChange={update("area_acres")}
            placeholder="2.0"
          />
        </div>
        <div className="field">
          <label htmlFor="soil">Soil type</label>
          {/* <input
            id="soil"
            value={form.soil_type}
            onChange={update("soil_type")}
            placeholder="e.g. Red Loam"
          /> */}
          <select
            id="soil"
            value={form.soil_type}
            onChange={update("soil_type")}
          >
            +{" "}
            {SOIL_TYPES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
            +{" "}
          </select>
        </div>
      </div>
      <div className="actions">
        <button className="btn-primary" type="submit" disabled={loading}>
          {loading ? "Generating…" : "Generate Today's Farm Intelligence"}
        </button>
      </div>
    </form>
  );
}
