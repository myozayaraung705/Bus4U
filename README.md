# Yangon YBS Navigator

A lightweight, and **web application(using serverless architecture)** designed to help daily users, travelers, and foreigners navigate the Yangon Bus Service (YBS) system seamlessly. Built with an offline-first data approach and optimized for mobile-first user experiences.

Live Demo: [https://myozayaraung705.github.io/Bus4U/]

The interface uses a green-and-white, map-first layout with a desktop trip panel and an expandable mobile bottom sheet. Search destinations in English or Burmese, use popular destination shortcuts, or browse all YBS routes.

On desktop and tablet, use the chevron tab on the trip panel's right edge to minimize or reopen it. The panel slides away without resetting your search or journey; reduced-motion preferences are respected.

On phones, hold the sheet's top handle and drag down to close it, or drag up to reopen or expand it. The sheet follows your finger and snaps into place on release. A “Plan a trip” handle stays visible when closed. Tapping the handle also opens/closes the sheet, and keyboard users can use the arrow keys, Home, and End. Searches and journeys are retained.

For a local preview, run `python -m http.server 4173` in the project folder and open `http://localhost:4173`. Keep `index.html`, `styles.css`, `sheet-gestures.js`, and `ybs_data.json` together when deploying.

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
