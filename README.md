# Yangon YBS Navigator

A lightweight, and **web application(using serverless architecture)** designed to help daily users, travelers, and foreigners navigate the Yangon Bus Service (YBS) system seamlessly. Built with an offline-first data approach and optimized for mobile-first user experiences.

Live Demo: [https://myozayaraung705.github.io/Bus4U/]


---

##  Tech Stack and Spec 

To achieve a 100% free hosting structure with zero server costs, this application relies completely on client-side browser processing:

*   **Frontend UI:** HTML5, Tailwind CSS (via CDN)
*   **Mapping & Routing Engine:** Leaflet.js with MapLibre GL, OpenFreeMap basemaps (OpenStreetMap/OpenMapTiles data), and FOSSGIS routing
*   **Core Logic:** Native Vanilla JavaScript (Zero external heavy frameworks)
*   **Data Architecture:** High-density, relational-static JSON (`ybs_data.json`).

Basemaps use the [OpenFreeMap public service](https://openfreemap.org/quick_start/) without an API key. The app does not request tiles from `tile.openstreetmap.org`. Keep the map attribution visible. If the basemap cannot load, a retry notice appears while local stop search and route overlays remain usable. Map backgrounds and road directions require an internet connection; the embedded transit dataset remains available offline.

## 📄 Raw Data Attribution & Licensing

The master dataset (`ybs_data.json`) used in this application is curated, deduplicated, and engineered independently by me, utilizing raw transit data from the following open-source resources:

1.  **First Raw Dataset:** Distributed under the **YRTA Open Data License 1.0**. All retrieval, modification, and distribution of this data comply with the permissions and constraints of the YRTA framework. [https://github.com/eimg/ybs-data-json]
2.  **Second Raw Dataset:** Licensed under **CC-BY-SA-4.0**. [https://github.com/thantthet/YBS-Data]

### 🛠️ My Data Refinement Work
While the baseline coordinates and labels belong to the respective raw data owners, **no direct copies were used**. In compliance with the CC-BY-SA-4.0 ShareAlike terms, my refined derivative dataset is also shared openly for the community.

## 🤝 Contributing

Contributions to improve YBS route sequences, translation updates, or custom UI patches are highly welcome! Feel free to open an Issue or submit a Pull Request.
