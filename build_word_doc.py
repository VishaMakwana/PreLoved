import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_shading(cell, color_hex):
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=180, right=180):
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    cell._tc.get_or_add_tcPr().append(tcMar)

def set_table_borders(table, color="D1D5DB", sz="6"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'''
        <w:tblBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:left w:val="none"/>
            <w:right w:val="none"/>
            <w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:insideV w:val="none"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders)

def add_callout(doc, title, text, bg_hex="F0FDF4", border_hex="10B981"):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_shading(cell, bg_hex)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="none"/>
            <w:left w:val="single" w:sz="32" w:space="0" w:color="{border_hex}"/>
            <w:bottom w:val="none"/>
            <w:right w:val="none"/>
        </w:tcBorders>
    ''')
    cell._tc.get_or_add_tcPr().append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    run_t = p.add_run(f"📌 {title}\n")
    run_t.font.bold = True
    run_t.font.name = "Segoe UI"
    run_t.font.size = Pt(10.5)
    run_t.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    
    run_b = p.add_run(text)
    run_b.font.name = "Segoe UI"
    run_b.font.size = Pt(9.5)
    run_b.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
    
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(0)
    p_after.paragraph_format.space_after = Pt(4)

def add_algorithm_box(doc, algo_num, algo_name, objective, steps, inputs=None, outputs=None):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_shading(cell, "F8FAFC")
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="2563EB"/>
            <w:bottom w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
            <w:right w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
        </w:tcBorders>
    ''')
    cell._tc.get_or_add_tcPr().append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    
    # Title
    r_title = p.add_run(f"ALGORITHM {algo_num}: {algo_name}\n")
    r_title.font.name = "Segoe UI"
    r_title.font.size = Pt(11.0)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    
    # Objective
    r_obj_label = p.add_run("• Objective: ")
    r_obj_label.font.name = "Segoe UI"
    r_obj_label.font.size = Pt(9.5)
    r_obj_label.font.bold = True
    r_obj_label.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    
    r_obj = p.add_run(f"{objective}\n")
    r_obj.font.name = "Segoe UI"
    r_obj.font.size = Pt(9.5)
    r_obj.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
    
    # Inputs & Outputs if provided
    if inputs:
        r_in_l = p.add_run("• Inputs: ")
        r_in_l.font.name = "Segoe UI"
        r_in_l.font.size = Pt(9.5)
        r_in_l.font.bold = True
        r_in_l.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
        r_in = p.add_run(f"{inputs}\n")
        r_in.font.name = "Segoe UI"
        r_in.font.size = Pt(9.5)
        r_in.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
        
    if outputs:
        r_out_l = p.add_run("• Outputs / Result: ")
        r_out_l.font.name = "Segoe UI"
        r_out_l.font.size = Pt(9.5)
        r_out_l.font.bold = True
        r_out_l.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
        r_out = p.add_run(f"{outputs}\n\n")
        r_out.font.name = "Segoe UI"
        r_out.font.size = Pt(9.5)
        r_out.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
    else:
        p.add_run("\n")
        
    # Step-by-step logical sequence
    r_steps_header = p.add_run("Procedural Execution Steps:\n")
    r_steps_header.font.name = "Segoe UI"
    r_steps_header.font.size = Pt(9.5)
    r_steps_header.font.bold = True
    r_steps_header.font.color.rgb = RGBColor(0x1E, 0x40, 0xAF)
    
    for idx, (step_title, step_desc) in enumerate(steps, start=1):
        r_step_num = p.add_run(f"  Step {idx}. {step_title}: ")
        r_step_num.font.name = "Segoe UI"
        r_step_num.font.size = Pt(9.0)
        r_step_num.font.bold = True
        r_step_num.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
        
        r_step_body = p.add_run(f"{step_desc}\n")
        r_step_body.font.name = "Segoe UI"
        r_step_body.font.size = Pt(9.0)
        r_step_body.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
        
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(0)
    p_after.paragraph_format.space_after = Pt(4)

def add_styled_table(doc, headers, data, col_widths=None):
    table = doc.add_table(rows=len(data) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table, color="CBD5E1", sz="6")
    
    # Header Row
    hdr_row = table.rows[0]
    trPr = hdr_row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    
    for i, h_text in enumerate(headers):
        cell = hdr_row.cells[i]
        set_cell_shading(cell, "1E3A8A") # Navy
        set_cell_margins(cell, top=140, bottom=140, left=140, right=140)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(h_text)
        run.font.bold = True
        run.font.name = "Segoe UI"
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        
    # Data Rows
    for r_idx, row_data in enumerate(data):
        row = table.rows[r_idx + 1]
        bg_color = "F8FAFC" if (r_idx % 2 == 1) else "FFFFFF"
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            set_cell_shading(cell, bg_color)
            set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(str(val))
            run.font.name = "Segoe UI"
            run.font.size = Pt(9.0)
            run.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
            
    if col_widths:
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = Inches(width)
                
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(0)
    p_after.paragraph_format.space_after = Pt(6)

def build_document():
    doc = Document()
    
    # Page setup - Margins 0.8 in
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
    # Styles setup
    style_normal = doc.styles['Normal']
    font_normal = style_normal.font
    font_normal.name = 'Segoe UI'
    font_normal.size = Pt(10.0)
    font_normal.color.rgb = RGBColor(0x33, 0x41, 0x55)
    
    # -----------------------------
    # COVER / HEADER BANNER
    # -----------------------------
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(10)
    title_p.paragraph_format.space_after = Pt(2)
    run_pre = title_p.add_run("GIGBRIDGE SYSTEM ARCHITECTURE & MASTER DOCUMENTATION\n")
    run_pre.font.name = "Segoe UI"
    run_pre.font.size = Pt(10.5)
    run_pre.font.bold = True
    run_pre.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)
    
    run_title = title_p.add_run("PreLoved – Second-Hand Goods Marketplace")
    run_title.font.name = "Segoe UI"
    run_title.font.size = Pt(22.0)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    
    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_before = Pt(2)
    sub_p.paragraph_format.space_after = Pt(14)
    run_sub = sub_p.add_run("Complete End-to-End System Specifications, Logic Algorithms, Relational Schema, Live Feed Engine & 5-Day Agile Sprint Plan")
    run_sub.font.name = "Segoe UI"
    run_sub.font.size = Pt(11.0)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
    
    add_callout(
        doc,
        "Day 1 Official Deliverable (Conceptual & Algorithmic Documentation)",
        "This document provides the complete theoretical, functional, and algorithmic blueprint for the PreLoved platform. It strictly presents structured business logic, system flows, and technical algorithms without code-side portions, serving as the official reference for the 5-day implementation sprint.",
        bg_hex="EFF6FF",
        border_hex="3B82F6"
    )
    
    # -----------------------------
    # SECTION 1: EXECUTIVE SUMMARY
    # -----------------------------
    h1 = doc.add_heading(level=1)
    r = h1.add_run("1. Executive Summary & Project Identification")
    r.font.name = "Segoe UI"
    r.font.size = Pt(14.0)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    
    p = doc.add_paragraph(
        "PreLoved is a modern, responsive, hyper-local consumer-to-consumer (C2C) marketplace designed to make the buying and selling of pre-owned goods—including mobile phones, laptops, books, furniture, and daily utility items—transparent, dependable, and efficient. The platform bridges local buyers and sellers, enabling peer-to-peer discovery, price negotiations, direct messaging, and community moderation within a unified digital environment."
    )
    p.paragraph_format.space_after = Pt(6)
    
    summary_headers = ["Project Parameter", "Technical & Operational Specification"]
    summary_data = [
        ["Project Title", "GigBridge – PreLoved: Second-Hand Goods Marketplace"],
        ["Primary Domain", "Hyper-Local Sustainable Commerce / C2C Second-Hand Goods Trading"],
        ["Platform Architecture", "Decoupled Model-View-Template (MVT) Pattern with Asynchronous Delta Feeds"],
        ["Server Environment", "Python 3.11 Enterprise Runtime, Django 5.x Framework Engine"],
        ["Database Tier", "SQLite3 (Relational ACID-compliant storage) / PostgreSQL compatible"],
        ["Client Presentation", "HTML5, CSS3, Modern Bootstrap 5.3, Modern Vanilla JavaScript (ES6+)"],
        ["Image Processing", "Pillow (PIL) Automated Image Normalization, EXIF Stripping, WebP/JPEG Pipeline"],
        ["Real-Time Core", "Live Responsive Delta Synchronization Engine (1-2s delay between users X1 ➔ X2, X3)"],
        ["Design Language", "Minimalist Clean Glassmorphism inspired by 21st.dev and Awwwards.com"],
        ["Sprint Timeline", "5-Day Structured Agile Delivery (Day 1: Documentation, Days 2-5: Implementation)"]
    ]
    add_styled_table(doc, summary_headers, summary_data, [2.2, 4.3])
    
    # -----------------------------
    # SECTION 2: LIVE RESPONSIVE ENGINE (USER'S NEW FEATURE)
    # -----------------------------
    h1 = doc.add_heading(level=1)
    r = h1.add_run("2. Real-Time Live Responsive Feed Engine (X1 ➔ X2, X3)")
    r.font.name = "Segoe UI"
    r.font.size = Pt(14.0)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    
    doc.add_paragraph(
        "A critical requirement for PreLoved is live marketplace reactivity: when User X1 uploads a new listing (for example, a smartphone named 'xyz'), all other active users (such as User X2 and User X3) currently viewing the marketplace catalog or category feeds must see the new item appear automatically on their screens within 1 to 2 seconds, without manually refreshing the webpage."
    )
    
    add_callout(
        doc,
        "Architectural Solution & Operational Mechanism",
        "To achieve instantaneous visibility without overloading the server or causing layout jitter, PreLoved employs a cursor-based delta synchronization architecture. Clients maintain an in-memory cursor of the latest listing ID they have rendered. Every 2 seconds, the client sends a lightweight probe requesting only records with an ID strictly greater than that cursor. When new items are published, the server immediately delivers the new item payload, and the client smoothly inserts the new item card at the top of the feed using micro-animated transitions.",
        bg_hex="ECFDF5",
        border_hex="10B981"
    )
    
    p = doc.add_paragraph("Key Architectural Advantages of the Delta Feed Engine:")
    p.paragraph_format.space_after = Pt(2)
    bullets = [
        ("Sub-Millisecond Query Execution: ", "Because queries utilize the primary key index (ID > Cursor), the database executes an instant index-seek with virtually zero CPU utilization."),
        ("Bandwidth Efficiency: ", "If no new listings have been uploaded by User X1 or any other seller, the server returns an empty 32-byte response, ensuring zero unnecessary bandwidth consumption."),
        ("Preservation of User Scroll State: ", "Rather than resetting or re-rendering the entire catalog, newly arrived items are prepended fluidly to the top of the grid using CSS slide-down animations without disrupting the buyer's current scroll position."),
        ("Automatic Tab Throttling: ", "When a user switches browser tabs or minimizes the window, the client detects the hidden visibility state and suspends polling to conserve client device battery and network resources.")
    ]
    for b_title, b_desc in bullets:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_before = Pt(1)
        bp.paragraph_format.space_after = Pt(2)
        r_bt = bp.add_run(b_title)
        r_bt.font.bold = True
        r_bt.font.color.rgb = RGBColor(0x1E, 0x40, 0xAF)
        bp.add_run(b_desc)
        
    doc.add_paragraph()
    
    # -----------------------------
    # SECTION 3: SYSTEM MODULES
    # -----------------------------
    h1 = doc.add_heading(level=1)
    r = h1.add_run("3. System Modules & Functional Breakdown")
    r.font.name = "Segoe UI"
    r.font.size = Pt(14.0)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    
    h2 = doc.add_heading(level=2)
    r = h2.add_run("3.1 User Module (Buyer & Seller Capabilities)")
    r.font.name = "Segoe UI"
    r.font.size = Pt(12.0)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)
    
    user_mod_headers = ["Sub-Module", "Detailed Operational Capabilities"]
    user_mod_data = [
        ["Authentication & Identity", "User registration with email/phone verification, session management, secure login/logout, avatar image upload, and trading location assignment."],
        ["Seller Listing Studio", "Multi-step wizard allowing sellers to upload multiple high-resolution photos, select categories, define condition ratings (Brand New, Like New, Good, Fair), set asking prices, and specify neighborhood locations."],
        ["Listing Lifecycle Management", "Full control over published goods: edit descriptions and prices, mark items as 'Deal Pending' during negotiations, and officially mark items as 'Sold' to archive them."],
        ["Catalog Search & Dynamic Filtering", "Instant multi-factor search across listing titles and descriptions, category tree navigation, dynamic price slider boundaries, condition filters, and city selection."],
        ["Live Feed Ingestion", "Background reactive channel that receives newly published items within 1-2 seconds and renders them smoothly into the marketplace grid."],
        ["Wishlist & Favorites Engine", "One-click toggle to save prospective items to a private wishlist with real-time heart bounce micro-interactions and quick access from the navigation bar."],
        ["Direct Buyer-Seller Chat", "Contextual direct messaging between interested buyers and the seller, scoped specifically to the item of interest with read receipts and timestamps."],
        ["Price Offer Negotiation", "Structured counter-offer framework where buyers submit specific price proposals. Sellers can accept, reject, or wait for better bids with automated item status updates."],
        ["Community Report Submission", "Flagging mechanism allowing users to report suspicious, counterfeit, misleading, or prohibited listings with categorized reasons and narrative explanations."]
    ]
    add_styled_table(doc, user_mod_headers, user_mod_data, [2.0, 4.5])
    
    h2 = doc.add_heading(level=2)
    r = h2.add_run("3.2 Admin Governance Module")
    r.font.name = "Segoe UI"
    r.font.size = Pt(12.0)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)
    
    admin_mod_headers = ["Governance Component", "Administrative Scope & Controls"]
    admin_mod_data = [
        ["Category Governance", "Create, edit, reorder, activate, and deactivate marketplace categories; assign visual Bootstrap icons and manage category hierarchies."],
        ["Listing Moderation Hub", "Unified administrative queue displaying all flagged, reported, or high-risk listings with one-click approval, modification, or takedown actions."],
        ["Automated Risk Concealment", "Automatic system safety rule: any listing accumulating 3 or more independent community reports is automatically removed from public feeds pending staff review."],
        ["User Sanctioning & Account Bans", "Authority to issue formal warnings, suspend account privileges, or permanently ban fraudulent buyers or sellers with automated notification dispatches."],
        ["Platform Analytics & Dashboard", "Real-time key performance indicators: total active listings, gross platform transaction estimates, user sign-up velocity, and unresolved report queues."]
    ]
    add_styled_table(doc, admin_mod_headers, admin_mod_data, [2.0, 4.5])
    
    # -----------------------------
    # SECTION 4: CORE ALGORITHMS & LOGICAL PROCEDURES
    # -----------------------------
    h1 = doc.add_heading(level=1)
    r = h1.add_run("4. Core Algorithms & Logical Procedures")
    r.font.name = "Segoe UI"
    r.font.size = Pt(14.0)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    
    doc.add_paragraph(
        "This section details the theoretical and logical algorithms powering the PreLoved platform. Each algorithm is defined through rigorous step-by-step procedures, specifying input preconditions, operational transformations, state validations, and output guarantees."
    )
    
    # ALGORITHM 1
    algo1_steps = [
        ("Client Initialization", "Upon page load, the client browser parses the highest listing ID present in the initial server-rendered grid and initializes the tracking cursor variable (Current_Cursor)."),
        ("Inactivity & Tab State Verification", "Before initiating a scheduled query, the client checks the Page Visibility API. If the browser tab is minimized or hidden, the poll is skipped to conserve system resources."),
        ("Asynchronous Delta Query Formulation", "At regular 2-second intervals, the client transmits an asynchronous request to the feed endpoint, passing the Current_Cursor along with any active category and city filter parameters."),
        ("Server-Side Index Seek", "The backend server queries the listings database using an indexed condition: ID strictly greater than Current_Cursor, status equals 'ACTIVE', and moderation flag equals false."),
        ("Batch Clamping & Normalization", "The server clamps the matched records to a maximum batch size of 20 items to prevent network saturation and serializes the listing metadata (title, price, condition, city, seller name, image URL)."),
        ("Response Assembly & Cursor Advancement", "The server calculates the new maximum ID from the batch. If new items exist, it returns the items array along with the New_Cursor; otherwise, it returns an empty payload."),
        ("Client DOM Prepending & Animation Trigger", "The client browser iterates through the received items in reverse chronological order, constructs the card structure, prepends it to the top of the grid, and applies an entrance transition animation."),
        ("Live Alert Notification", "The client updates its tracking cursor to New_Cursor and triggers a temporary floating toast alert notifying the user of newly arrived items.")
    ]
    add_algorithm_box(
        doc, 
        "1", 
        "Real-Time Live Feed Delta Synchronization",
        "Propagate newly published listings from User X1 to active User X2 and User X3 sessions within 1-2 seconds without full-page reloads.",
        algo1_steps,
        inputs="Client Cursor ID (integer), Category Filter (optional), City Filter (optional)",
        outputs="Array of newly published listings, Updated Cursor ID, Dynamic DOM Card Ingestion"
    )
    
    # ALGORITHM 2
    algo2_steps = [
        ("Base Candidate Filtering", "Retrieve the initial universe of listings restricted strictly to records with status equal to 'ACTIVE' and visibility flag set to true."),
        ("Exact Attribute Partitioning", "Apply categorical and geographic filters. If a category slug is specified, filter by exact category match; if a city is provided, filter using case-insensitive match."),
        ("Continuous Numeric Boundary Clamping", "Enforce price bounds. If minimum price is defined, constrain price >= minimum; if maximum price is defined, constrain price <= maximum."),
        ("Condition State Filtering", "If specific item conditions (e.g., 'Brand New', 'Like New') are selected by the buyer, filter records matching the requested condition tags."),
        ("Search String Tokenization", "If a keyword query is provided, sanitize and tokenize the search string into individual alphanumeric terms, discarding common stop words."),
        ("Multi-Field Weighted Relevance Scoring", "Evaluate each record against the search tokens: Title matches are assigned a weight factor of 3.0, while Description matches are assigned a weight factor of 1.0. Compute the composite relevance score for each candidate."),
        ("Hierarchical Multi-Criteria Sorting", "Sort the qualified candidate set: If relevance search is active, order primarily by descending relevance score, secondarily by creation date. If user selected explicit price sorting, order by price ascending or descending."),
        ("Deterministic Pagination Slicing", "Apply pagination offsets (default: 16 items per page) to yield consistent, high-performance catalog results.")
    ]
    add_algorithm_box(
        doc,
        "2",
        "Multi-Factor Catalog Search, Relevance Scoring & Spatial Filtering",
        "Provide fast, accurate, and multi-criteria product discovery combining full-text relevance, categorical boundaries, and geographic locality.",
        algo2_steps,
        inputs="Keyword query string, Category slug, Minimum/Maximum price boundaries, Condition array, Target city, Sort preference",
        outputs="Ranked, filtered, and paginated list of matching product listings"
    )
    
    # ALGORITHM 3
    algo3_steps = [
        ("Offer Inception & Self-Dealing Guard", "A registered buyer submits a price offer for an active listing. The system verifies that the buyer is not the seller of the item; self-offers are strictly rejected."),
        ("Price Sanity & Boundary Validation", "The proposed amount must fall within logical boundaries: minimum 10% of the listed price and maximum 150% of the listed price to prevent negative or absurd values."),
        ("Pending State Assignment", "The offer is registered with status 'PENDING', and an automated alert is routed to the seller's notifications and active chat thread."),
        ("Seller Evaluation & Branching Decision", "The seller reviews the offer and selects one of three actions: Accept, Reject, or Propose Counter-Offer."),
        ("Transition to 'ACCEPTED' State", "If the seller accepts: The offer status updates to 'ACCEPTED'. The listing status automatically updates from 'ACTIVE' to 'DEAL_PENDING' to prevent duplicate offers. All other competing pending offers receive an automated notification."),
        ("Transition to 'REJECTED' State", "If the seller rejects: The offer status updates to 'REJECTED'. The listing remains 'ACTIVE' for other prospective buyers."),
        ("Buyer Withdrawal Transition", "Prior to seller acceptance, the buyer retains the right to withdraw the offer, transitioning the state to 'CANCELLED'."),
        ("Final Deal Closure ('SOLD' Transition)", "Following physical inspection and handoff, the seller clicks 'Mark as Sold'. The listing transitions to 'SOLD', all remaining pending or countered offers transition to 'EXPIRED', and the item is permanently delisted from live discovery feeds.")
    ]
    add_algorithm_box(
        doc,
        "3",
        "Price Offer Negotiation Finite State Automaton (FSM)",
        "Enforce transactional consistency, eliminate race conditions, and govern the formal price negotiation lifecycle between buyers and sellers.",
        algo3_steps,
        inputs="Buyer identity, Listing reference, Proposed purchase amount, Seller decision action",
        outputs="Deterministic state transition (PENDING ➔ ACCEPTED / REJECTED / CANCELLED ➔ SOLD / EXPIRED)"
    )
    
    # ALGORITHM 4
    algo4_steps = [
        ("Binary Stream Verification", "Receive user-uploaded image stream and verify header magic bytes to ensure file is an authentic raster graphic (JPEG, PNG, WebP) and not an executable binary."),
        ("EXIF Orientation Transpose", "Read camera metadata orientation tags (EXIF tag 274) and rotate the image pixel matrix accordingly so mobile camera photos render upright."),
        ("Privacy & Geolocation Scrubbing", "Strip all embedded EXIF metadata, including GPS coordinates, camera serial numbers, and capture timestamps, completely shielding user location privacy."),
        ("Color Space Standardisation", "Examine image mode. If RGBA or Palette mode is detected, convert the matrix to standard 24-bit sRGB color space to ensure cross-browser rendering fidelity."),
        ("Proportional Dimension Clamping", "Evaluate pixel dimensions. If width exceeds 1440px or height exceeds 1080px, calculate the aspect-ratio preserved scaling factor and downscale the image using high-quality Lanczos resampling."),
        ("Modern WebP Lossy Compression", "Encode the normalized image into modern WebP format utilizing 82% quality target with dynamic Huffman coding, typically reducing file size by 65-80% compared to raw JPEG."),
        ("Secure In-Memory Buffer Re-Encapsulation", "Assign a cryptographically secure UUIDv4 filename, package the compressed binary into an in-memory file structure, and commit to local media directory storage.")
    ]
    add_algorithm_box(
        doc,
        "4",
        "Automated Image Optimization & EXIF Privacy Sanitization Pipeline",
        "Standardize user-submitted photos, reduce storage overhead, accelerate page load speeds, and permanently strip sensitive GPS location metadata.",
        algo4_steps,
        inputs="Raw multipart image upload stream from user browser/mobile device",
        outputs="Sanitized, oriented, Lanczos-scaled, compressed WebP image stored with UUID identifier"
    )
    
    # ALGORITHM 5
    algo5_steps = [
        ("Text Corpus Extraction & Normalization", "Combine listing title and description into a unified text string, convert all characters to lowercase, and strip punctuation marks."),
        ("Prohibited Lexicon Scanning", "Iterate through the platform's prohibited term dictionary (counterfeits, weapons, illicit substances, stolen goods). Each occurrence increments the listing's Risk Score by 50 points."),
        ("Price Anomaly Heuristic Evaluation", "Cross-reference detected high-value item keywords (e.g., flagship mobile phones) against listed asking prices. An asking price below 10% of typical market baseline increments the Risk Score by 30 points."),
        ("Seller Trust & Maturity Factor", "Examine seller account age and completed sales volume. A newly created account listing high-value items on day one increments the Risk Score by 10 points."),
        ("Automated Threshold Action", "If the composite Risk Score meets or exceeds 50 points, the system automatically sets the listing's visibility flag to false (hidden from public catalog) and queues an urgent incident in the Admin Moderation Hub."),
        ("Community Velocity Trigger", "Continuously monitor user report counts. If any active listing receives 3 or more independent reports from verified user accounts within a 24-hour window, the listing is automatically hidden from public search pending staff resolution.")
    ]
    add_algorithm_box(
        doc,
        "5",
        "Automated Content Moderation & Abuse Scoring Heuristics",
        "Protect the marketplace against counterfeit goods, spam, prohibited items, and malicious actors through automated risk detection and community velocity triggers.",
        algo5_steps,
        inputs="Listing text corpus, Listed price, Seller transaction history, User report logs",
        outputs="Numerical Risk Score, Automated Visibility Status (Active / Hidden Under Review), Admin Moderation Queue Entry"
    )
    
    # -----------------------------
    # SECTION 5: COMPLETE DATABASE SCHEMA
    # -----------------------------
    h1 = doc.add_heading(level=1)
    r = h1.add_run("5. Complete Database Schema & Data Dictionary")
    r.font.name = "Segoe UI"
    r.font.size = Pt(14.0)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    
    doc.add_paragraph(
        "The PreLoved database design adheres strictly to Third Normal Form (3NF), guaranteeing data integrity, zero update anomalies, and lightning-fast query response times across all catalog operations."
    )
    
    h2 = doc.add_heading(level=2)
    r = h2.add_run("5.1 Relational Entity Overview")
    r.font.name = "Segoe UI"
    r.font.size = Pt(11.5)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)
    
    schema_headers = ["Entity / Table Name", "Domain Responsibility", "Primary Relational Linkages"]
    schema_data = [
        ["CustomUser (users_customuser)", "Represents registered buyers, sellers, and administrators with trust flags and profiles.", "Parent to Listings, Wishlists, Offers, Messages, and Reports."],
        ["Category (listings_category)", "Lookup taxonomy for organizing items (Mobiles, Books, Furniture, etc.).", "One-to-Many parent to Listings."],
        ["Listing (listings_listing)", "Core marketplace item record containing pricing, condition, city, and status.", "Child of User and Category; Parent to Images, Offers, Wishlists, and Reports."],
        ["ListingImage (listings_listingimage)", "Stores WebP-optimized photo assets linked to specific item listings.", "Many-to-One child of Listing."],
        ["Wishlist (trading_wishlist)", "Stores saved bookmark associations between buyers and favorite items.", "Join entity linking User and Listing."],
        ["Offer (trading_offer)", "Records structured price bids, counter-offers, and negotiation states.", "Relates Buyer (User) to Target Listing."],
        ["Message (chat_message)", "Maintains chronological direct communication messages between trading parties.", "Relates Sender, Receiver, and context Listing."],
        ["Report (moderation_report)", "Tracks community grievance submissions and moderation audit logs.", "Relates Reporting User to Target Listing."],
        ["UserAuditLog (moderation_auditlog)", "Maintains immutable security and compliance audit trails of critical actions.", "Child of User."]
    ]
    add_styled_table(doc, schema_headers, schema_data, [2.0, 2.3, 2.2])
    
    h2 = doc.add_heading(level=2)
    r = h2.add_run("5.2 Data Dictionary: Core Item Listing Entity ('listings_listing')")
    r.font.name = "Segoe UI"
    r.font.size = Pt(11.5)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)
    
    listing_field_headers = ["Field Name", "Data Type", "Null / Blank", "Default Value", "Key / Domain Description"]
    listing_field_data = [
        ["id", "Big Integer (Auto)", "No", "Auto Increment", "Primary Key; functions as the sequential cursor for live feed polling"],
        ["seller_id", "Foreign Key (User)", "No", "None", "Foreign Key referencing publishing user; cascades on user deletion"],
        ["category_id", "Foreign Key (Category)", "No", "None", "Foreign Key referencing category lookup; deletion protected"],
        ["title", "Varchar (200)", "No", "None", "Descriptive headline of the item displayed on cards and search headers"],
        ["slug", "Varchar (250)", "No", "None", "Unique SEO-optimized URL identifier for product detail pages"],
        ["description", "Text", "No", "None", "Full product narrative detailing specifications, wear history, and included accessories"],
        ["price", "Decimal (10, 2)", "No", "None", "Asking price in Indian National Rupees (₹) with currency decimal precision"],
        ["condition", "Varchar (20)", "No", "'GOOD'", "Condition grade: BRAND_NEW, LIKE_NEW, GOOD, FAIR"],
        ["city", "Varchar (100)", "No", "None", "Geographic trading municipality for local face-to-face transactions"],
        ["location_area", "Varchar (150)", "Yes / Yes", "None", "Specific neighborhood or local landmark for meetup convenience"],
        ["status", "Varchar (20)", "No", "'ACTIVE'", "Lifecycle status: ACTIVE, DEAL_PENDING, SOLD, ARCHIVED"],
        ["is_flagged_hidden", "Boolean", "No", "False", "Safety concealment flag triggered by automated risk or reports"],
        ["view_count", "Positive Integer", "No", "0", "Engagement metric incremented on distinct product view impressions"],
        ["created_at", "Date-Time (TZ)", "No", "Current Time", "Publication timestamp utilized for chronological feed ordering"],
        ["updated_at", "Date-Time (TZ)", "No", "Current Time", "Timestamp of most recent price adjustment or modification"]
    ]
    add_styled_table(doc, listing_field_headers, listing_field_data, [1.4, 1.4, 0.9, 0.9, 1.9])
    
    # -----------------------------
    # SECTION 6: API SPECIFICATIONS
    # -----------------------------
    h1 = doc.add_heading(level=1)
    r = h1.add_run("6. REST & Real-Time API Endpoint Catalog")
    r.font.name = "Segoe UI"
    r.font.size = Pt(14.0)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    
    doc.add_paragraph(
        "PreLoved exposes clean, REST-compliant endpoints powering asynchronous client operations, real-time feed polling, wishlist toggling, direct messaging, and negotiation workflows:"
    )
    
    api_headers = ["HTTP", "Endpoint URI", "Access Level", "Parameters / Query", "Payload & Contract Description"]
    api_data = [
        ["GET", "/api/v1/feed/live/", "Public", "after_id (int), category (int)", "Returns JSON array of newly published listings created after the specified cursor ID, including pre-rendered card templates and new maximum cursor."],
        ["GET", "/api/v1/listings/", "Public", "q (str), min_price, max_price, city", "Returns paginated list of active listings matching multi-factor search criteria and filter parameters."],
        ["POST", "/api/v1/listings/create/", "Authenticated", "Multipart form data with photos", "Processes multi-photo uploads, executes Pillow WebP pipeline, and commits new item to active catalog."],
        ["POST", "/api/v1/listings/<id>/wishlist/", "Authenticated", "CSRF token header", "Toggles wishlist state for the calling user, returning boolean state and updated total favorite count."],
        ["POST", "/api/v1/listings/<id>/offers/", "Authenticated", "JSON: amount (decimal)", "Validates price sanity, creates pending offer record, and notifies the listing seller."],
        ["POST", "/api/v1/offers/<id>/respond/", "Seller Only", "JSON: decision ('ACCEPT'/'REJECT')", "Executes state transition, locks listing to 'DEAL_PENDING' if accepted, and notifies buyer."],
        ["GET", "/api/v1/chat/<listing_id>/", "Trading Parties", "None", "Retrieves chronological message history between the buyer and seller for the specified listing."],
        ["POST", "/api/v1/chat/<listing_id>/send/", "Trading Parties", "JSON: body (text)", "Appends new message, updates read receipts, and delivers real-time chat payload."],
        ["POST", "/api/v1/listings/<id>/report/", "Authenticated", "JSON: reason, details", "Registers community grievance against listing; triggers automated hiding if threshold reached."],
        ["POST", "/api/v1/admin/moderate/", "Staff / Admin", "JSON: listing_id, action", "Applies administrative sanctions: approve, remove listing, or permanently ban fraudulent user."]
    ]
    add_styled_table(doc, api_headers, api_data, [0.7, 1.8, 1.0, 1.4, 1.6])
    
    # -----------------------------
    # SECTION 7: UI/UX DESIGN SYSTEM SPECIFICATION
    # -----------------------------
    h1 = doc.add_heading(level=1)
    r = h1.add_run("7. UI/UX Design System Specification (21st.dev & Awwwards Aesthetic)")
    r.font.name = "Segoe UI"
    r.font.size = Pt(14.0)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    
    doc.add_paragraph(
        "To deliver an interface matching modern award-winning benchmarks (such as 21st.dev component showcases and Awwwards honorees), PreLoved departs from generic enterprise portals in favor of clean, typography-led minimalist glassmorphism:"
    )
    
    ui_headers = ["Design Attribute", "Design System Specification", "Target User Experience"]
    ui_data = [
        ["Color Palette", "Primary Brand: Electric Indigo (#4F46E5), Canvas Dark: Midnight Obsidian (#090D16), Surface Light: Pure Ceramic (#FFFFFF), Success Accent: Emerald Glow (#10B981).", "Provides high-contrast readability, clean visual hierarchies, and a premium modern aesthetic."],
        ["Glassmorphism Surfaces", "Backdrop-filter blur 16px, translucent surface background with subtle 1px border contrast (rgba(226, 232, 240, 0.8)).", "Delivers tactile depth, modern layering, and separation between feed cards and the canvas background."],
        ["Live Pulse Indicator", "Glowing green indicator badge next to 'Live Marketplace Feed' with continuous pulsing opacity animation.", "Immediately alerts users that the catalog is live and updating automatically in real time."],
        ["Card Micro-Interactions", "Subtle -4px vertical lift on hover combined with soft ambient box-shadow elevation and quick 200ms transition.", "Gives product cards an interactive, tactile feel inviting buyer exploration."],
        ["Live Card Insertion Animation", "Smooth slide-down and fade-in cubic-bezier transition when newly published listings appear.", "Seamlessly introduces new goods without visual jarring or page jumps."],
        ["Wishlist Heart Bounce", "Interactive spring scale animation (1.0 ➔ 1.3 ➔ 1.0) upon clicking the favorite heart icon.", "Provides instant, delightful visual affirmation of user action."],
        ["Adaptive Responsive Layout", "CSS Grid and Bootstrap 5.3 Flexbox: 1 column on mobile, 2 columns on tablets, 4 columns on desktop displays.", "Ensures consistent, ergonomic browsing across all mobile phones, tablets, and widescreen monitors."]
    ]
    add_styled_table(doc, ui_headers, ui_data, [1.5, 2.5, 2.5])
    
    # -----------------------------
    # SECTION 8: 5-DAY AGILE SPRINT ROADMAP
    # -----------------------------
    h1 = doc.add_heading(level=1)
    r = h1.add_run("8. 5-Day Delivery Sprint Roadmap & Milestones")
    r.font.name = "Segoe UI"
    r.font.size = Pt(14.0)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    
    roadmap_headers = ["Sprint Day", "Strategic Milestone", "Expected Deliverables & Outputs"]
    roadmap_data = [
        ["Day 1", "System Documentation & Architecture (Current Phase)", "Complete SRS, database ERD, theoretical algorithms, live feed engine specifications, API contracts, and formatted Word document deliverable."],
        ["Day 2", "Core Platform, Data Models & Admin Governance", "Django project structure setup, Custom User model, Category and Listing models, Pillow image processing pipeline, and admin moderation hub."],
        ["Day 3", "Marketplace Catalog, Search & Listing Studio", "Seller multi-photo listing submission studio, keyword search engine, dynamic price sliders, condition filters, and wishlist module."],
        ["Day 4", "Live Responsive Feed, Chat & Negotiations", "Implementation of the real-time live feed engine (1-2s delay X1 ➔ X2, X3), 1-on-1 buyer-seller direct messaging, and price offer negotiation state machine."],
        ["Day 5", "UI Polish, Verification & Final Deployment", "21st.dev/Awwwards visual refinement, cross-browser multi-user simulation testing, final validation, and code push to GitHub once permissions are confirmed."]
    ]
    add_styled_table(doc, roadmap_headers, roadmap_data, [1.1, 2.2, 3.2])
    
    add_callout(
        doc,
        "Repository & Version Control Policy",
        "Per project directives, all work remains completely local on this workstation. No commits or pushes will be transmitted to GitHub until official collaborator permissions are granted and explicit instructions are provided.",
        bg_hex="FFFBEB",
        border_hex="F59E0B"
    )
    
    # Save outputs
    out_path_root = r"C:\Users\samir\OneDrive\Desktop\BBT\GigBridge_PreLoved_Documentation.docx"
    out_path_docs = r"C:\Users\samir\OneDrive\Desktop\BBT\PreLoved-Django-P1\docs\GigBridge_PreLoved_Documentation.docx"
    
    doc.save(out_path_root)
    doc.save(out_path_docs)
    print(f"Successfully generated pure text/algorithm Word document:\n1. {out_path_root}\n2. {out_path_docs}")

if __name__ == "__main__":
    build_document()
