import streamlit as st
import pandas as pd
import json
from pathlib import Path

# ============================================================================
# DATA ACCESS - Reads from local data folder
# ============================================================================
DATA_DIR = Path(__file__).parent / "data"

def load_catalog():
    """Load catalog and filter to PARK_BELLEVUE songs only."""
    catalog_path = DATA_DIR / "catalog.json"
    if catalog_path.exists():
        with open(catalog_path, 'r') as f:
            full_catalog = json.load(f)
            # Filter to only Park Bellevue songs
            return [s for s in full_catalog.get("songs", []) if s.get("act_id") == "PARK_BELLEVUE"]
    return []

# Load songs (filtered to Park Bellevue only)
songs = load_catalog()

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(page_title="Park Bellevue Collective", page_icon="🏛️", layout="wide")

# Title
st.title("🏛️ Park Bellevue Collective")
st.caption("Publishing Catalog Portal • Read-Only")

# Sidebar Navigation
page = st.sidebar.radio("Go to", ["Dashboard", "All Songs", "Deployment Status"])

# ============================================================================
# DASHBOARD (Overview)
# ============================================================================
if page == "Dashboard":
    st.header("Catalog Overview")

    # Calculate metrics
    total_songs = len(songs)
    released_songs = sum(1 for s in songs if s.get('status') == 'released')
    mastered_songs = sum(1 for s in songs if s.get('status') == 'mastered')

    # Metrics Row
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Songs", total_songs)
    col2.metric("Released", released_songs)
    col3.metric("Mastered", mastered_songs)

    st.markdown("---")

    # Status Breakdown
    st.subheader("📊 Status Breakdown")
    status_counts = {}
    for s in songs:
        status = s.get('status', 'unknown').title()
        status_counts[status] = status_counts.get(status, 0) + 1

    if status_counts:
        cols = st.columns(len(status_counts))
        for i, (status, count) in enumerate(sorted(status_counts.items())):
            cols[i].metric(status, count)

    st.markdown("---")

    # Latest Activity / Recent Songs
    st.subheader("🎵 Song Catalog")
    if songs:
        table_data = []
        for s in songs:
            table_data.append({
                "Title": s['title'],
                "Artist": s.get('artist', 'Park Bellevue'),
                "Status": s.get('status', '-').title(),
                "Code": s.get('legacy_code', '-')
            })
        st.dataframe(pd.DataFrame(table_data), use_container_width=True)
    else:
        st.info("No songs in catalog yet.")

# ============================================================================
# ALL SONGS (Full Catalog View)
# ============================================================================
elif page == "All Songs":
    st.header("📀 Complete Catalog")

    if songs:
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All", "idea", "demo", "mixing", "mastered", "released"])
        with col2:
            search = st.text_input("Search by Title")

        # Apply filters
        filtered = songs
        if status_filter != "All":
            filtered = [s for s in filtered if s.get('status') == status_filter]
        if search:
            search_lower = search.lower()
            filtered = [s for s in filtered if search_lower in s.get('title', '').lower()]

        st.write(f"**Showing {len(filtered)} of {len(songs)} songs**")

        # Display table
        table_data = []
        for s in filtered:
            table_data.append({
                "Title": s['title'],
                "Artist": s.get('artist', 'Park Bellevue'),
                "Status": s.get('status', '-').title(),
                "Code": s.get('legacy_code', '-')
            })
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, height=500)
    else:
        st.info("No songs in catalog yet.")

# ============================================================================
# DEPLOYMENT STATUS (Read-Only View)
# ============================================================================
elif page == "Deployment Status":
    st.header("🚀 Deployment Status")
    st.caption("View where Park Bellevue songs are distributed and streaming")

    if not songs:
        st.info("No songs in catalog yet.")
    else:
        # Platform options for reference
        ALL_DISTRIBUTORS = ["DistroKid", "TuneCore", "CD Baby", "Amuse", "AWAL", "Ditto"]
        ALL_SYNC_LIBS = ["Songtradr", "Music Gateway", "Pond5", "Disco", "Taxi", "Musicbed", "Artlist"]
        ALL_STREAMING = ["Spotify", "Apple Music", "Amazon", "YouTube", "Tidal", "Deezer", "Pandora"]

        # Summary metrics
        songs_with_distribution = sum(1 for s in songs if s.get('deployments', {}).get('distribution'))
        songs_with_sync = sum(1 for s in songs if s.get('deployments', {}).get('sync_libraries'))
        songs_with_streaming = sum(1 for s in songs if s.get('deployments', {}).get('streaming'))

        col1, col2, col3 = st.columns(3)
        col1.metric("📦 On Distributors", songs_with_distribution)
        col2.metric("🎬 On Sync Libraries", songs_with_sync)
        col3.metric("🎧 On Streaming", songs_with_streaming)

        st.markdown("---")

        # Build the deployment table
        st.subheader("📋 All Songs - Deployment Details")

        table_data = []
        for s in songs:
            deps = s.get('deployments', {})
            dist_list = deps.get('distribution', [])
            sync_list = deps.get('sync_libraries', [])
            stream_list = deps.get('streaming', [])

            # Format with checkmarks
            def format_with_checks(platforms):
                if not platforms:
                    return "—"
                return " ".join([f"✅ {p}" for p in platforms])

            table_data.append({
                "Title": s['title'],
                "Status": s.get('status', '-').title(),
                "Publisher": "Park Bellevue Collective",
                "Distribution": format_with_checks(dist_list),
                "Sync Libraries": format_with_checks(sync_list),
                "Streaming": format_with_checks(stream_list)
            })

        st.dataframe(pd.DataFrame(table_data), use_container_width=True, height=400)

        # Platform Summary
        st.markdown("---")
        st.subheader("📊 Platform Coverage")

        # Count songs per platform
        platform_counts = {}
        for s in songs:
            deps = s.get('deployments', {})
            all_plats = deps.get('distribution', []) + deps.get('sync_libraries', []) + deps.get('streaming', [])
            for p in all_plats:
                platform_counts[p] = platform_counts.get(p, 0) + 1

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**📦 Distribution**")
            for p in ALL_DISTRIBUTORS:
                count = platform_counts.get(p, 0)
                if count > 0:
                    st.write(f"✅ {p}: {count} songs")

        with col2:
            st.markdown("**🎬 Sync Libraries**")
            for p in ALL_SYNC_LIBS:
                count = platform_counts.get(p, 0)
                if count > 0:
                    st.write(f"✅ {p}: {count} songs")

        with col3:
            st.markdown("**🎧 Streaming**")
            for p in ALL_STREAMING:
                count = platform_counts.get(p, 0)
                if count > 0:
                    st.write(f"✅ {p}: {count} songs")

        # Show "not deployed" note if nothing is deployed
        if not platform_counts:
            st.info("No deployment data yet. Songs will appear here once deployed to platforms.")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption("© 2026 Park Bellevue Collective • Read-Only Portal")
