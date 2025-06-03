# app.py - Streamlit version of your calorie tracker
# Deploy for FREE at share.streamlit.io

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import json
import os
import zipfile
from io import BytesIO

# Set page config
st.set_page_config(
    page_title="Calorie & Weight Tracker",
    page_icon="🥗",
    layout="wide"
)

# Exercise calorie rates
EXERCISE_RATES = {
    "Walk 2mph": 2.368,
    "Walk 3mph": 2.868,
    "Walk 4mph": 4.788,
    "Elliptical": 4.788,
    "Weights": 4.85
}

# Initialize session state for data persistence
if 'food_db' not in st.session_state:
    st.session_state.food_db = pd.DataFrame({
        'Food': ['Apple', 'Banana', 'Chicken Breast', 'Rice (cooked)', 'Bread slice'],
        'CaloriesPerGram': [0.52, 0.89, 1.65, 1.30, 2.65],
        'CaloriesPerUnit': [95, 105, 165, 205, 79]
    })

if 'calorie_log' not in st.session_state:
    st.session_state.calorie_log = pd.DataFrame(
        columns=['Date', 'Food', 'Amount', 'Unit', 'Calories']
    )

if 'weight_log' not in st.session_state:
    st.session_state.weight_log = pd.DataFrame(
        columns=['Date', 'Weight']
    )

if 'exercise_log' not in st.session_state:
    st.session_state.exercise_log = pd.DataFrame(
        columns=['Date', 'Exercise', 'Minutes', 'CaloriesBurned']
    )

if 'notes_log' not in st.session_state:
    st.session_state.notes_log = pd.DataFrame(
        columns=['Date', 'Notes']
    )

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Log Entry", "Food Database", "Analytics", "Export Data"])

# Function to save data to browser storage (for persistence)
def save_to_browser():
    # Streamlit Cloud automatically persists session state
    pass

# Log Entry Page
if page == "Log Entry":
    st.title("📝 Log Food & Weight")
    
    # Date picker
    selected_date = st.date_input("Date", value=date.today(), max_value=date.today())
    
    # Food Entry Section
    st.header("🍎 Food Entry")
    
    col1, col2 = st.columns(2)
    with col1:
        multi_day = st.checkbox("Multi-day entry (meal prep mode)")
    
    if multi_day:
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=date.today())
        with col2:
            end_date = st.date_input("End Date", value=date.today() + timedelta(days=6))
    
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
    
    with col1:
        food_list = st.session_state.food_db['Food'].tolist()
        selected_food = st.selectbox("Food", [""] + food_list)
    
    with col2:
        amount = st.number_input("Amount", min_value=0.0, step=0.1)
    
    with col3:
        unit = st.selectbox("Unit", ["grams", "units"])
    
    with col4:
        st.write("")  # Spacer
        st.write("")  # Spacer
        add_food = st.button("Add Food", type="primary")
    
    if add_food and selected_food and amount > 0:
        food_info = st.session_state.food_db[st.session_state.food_db['Food'] == selected_food].iloc[0]
        
        if unit == "grams":
            calories = amount * food_info['CaloriesPerGram']
        else:
            calories = amount * food_info['CaloriesPerUnit']
        
        if multi_day:
            dates_to_add = pd.date_range(start=start_date, end=end_date)
            for date_to_add in dates_to_add:
                new_entry = pd.DataFrame({
                    'Date': [date_to_add.date()],
                    'Food': [selected_food],
                    'Amount': [amount],
                    'Unit': [unit],
                    'Calories': [round(calories, 0)]
                })
                st.session_state.calorie_log = pd.concat([st.session_state.calorie_log, new_entry], ignore_index=True)
            st.success(f"Food entry added for {len(dates_to_add)} days!")
        else:
            new_entry = pd.DataFrame({
                'Date': [selected_date],
                'Food': [selected_food],
                'Amount': [amount],
                'Unit': [unit],
                'Calories': [round(calories, 0)]
            })
            st.session_state.calorie_log = pd.concat([st.session_state.calorie_log, new_entry], ignore_index=True)
            st.success("Food entry added!")
    
    # Quick Calorie Entry
    st.header("⚡ Quick Calorie Entry")
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        free_food = st.text_input("Food Description", placeholder="e.g., Restaurant meal")
    
    with col2:
        free_calories = st.number_input("Calories", min_value=0, step=1, key="free_cal")
    
    with col3:
        st.write("")  # Spacer
        st.write("")  # Spacer
        add_free = st.button("Add Calories", type="secondary")
    
    if add_free and free_food and free_calories > 0:
        new_entry = pd.DataFrame({
            'Date': [selected_date],
            'Food': [f"{free_food} (Quick Entry)"],
            'Amount': [1],
            'Unit': ["entry"],
            'Calories': [free_calories]
        })
        st.session_state.calorie_log = pd.concat([st.session_state.calorie_log, new_entry], ignore_index=True)
        st.success("Quick calorie entry added!")
    
    # Weight Entry
    st.header("⚖️ Weight Entry")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        weight = st.number_input("Body Weight (kg)", min_value=0.0, step=0.1)
    
    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        add_weight = st.button("Log Weight", type="secondary")
    
    if add_weight and weight > 0:
        # Check if weight already logged for this date
        existing = st.session_state.weight_log[st.session_state.weight_log['Date'] == selected_date]
        
        if not existing.empty:
            st.session_state.weight_log.loc[st.session_state.weight_log['Date'] == selected_date, 'Weight'] = weight
        else:
            new_entry = pd.DataFrame({
                'Date': [selected_date],
                'Weight': [weight]
            })
            st.session_state.weight_log = pd.concat([st.session_state.weight_log, new_entry], ignore_index=True)
        st.success("Weight logged!")
    
    # Exercise Entry
    st.header("🏃 Exercise Entry")
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        exercise = st.selectbox("Exercise Type", list(EXERCISE_RATES.keys()))
    
    with col2:
        minutes = st.number_input("Minutes", min_value=0, value=30, step=1)
    
    with col3:
        st.write("")  # Spacer
        st.write("")  # Spacer
        add_exercise = st.button("Log Exercise", type="primary")
    
    if add_exercise and minutes > 0:
        calories_burned = round(EXERCISE_RATES[exercise] * minutes, 0)
        new_entry = pd.DataFrame({
            'Date': [selected_date],
            'Exercise': [exercise],
            'Minutes': [minutes],
            'CaloriesBurned': [calories_burned]
        })
        st.session_state.exercise_log = pd.concat([st.session_state.exercise_log, new_entry], ignore_index=True)
        st.success(f"Exercise logged! {calories_burned} calories burned!")
    
    # Daily Notes
    st.header("📝 Daily Notes")
    
    # Check if notes exist for this date
    existing_notes = st.session_state.notes_log[st.session_state.notes_log['Date'] == selected_date]
    default_notes = existing_notes.iloc[0]['Notes'] if not existing_notes.empty else ""
    
    notes = st.text_area("Notes", value=default_notes, 
                         placeholder="Add any notes about your day, meals, how you're feeling, etc.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Notes", type="secondary"):
            if notes:
                if not existing_notes.empty:
                    st.session_state.notes_log.loc[st.session_state.notes_log['Date'] == selected_date, 'Notes'] = notes
                else:
                    new_entry = pd.DataFrame({
                        'Date': [selected_date],
                        'Notes': [notes]
                    })
                    st.session_state.notes_log = pd.concat([st.session_state.notes_log, new_entry], ignore_index=True)
                st.success("Notes saved!")
    
    # Today's Entries
    st.header("📊 Today's Entries")
    
    # Food entries
    st.subheader("Food")
    today_food = st.session_state.calorie_log[st.session_state.calorie_log['Date'] == selected_date]
    if not today_food.empty:
        st.dataframe(today_food[['Food', 'Amount', 'Unit', 'Calories']])
        st.write(f"**Total Calories: {today_food['Calories'].sum()}**")
        
        # Delete food entries
        if st.button("Delete Selected Food Entry"):
            if len(today_food) > 0:
                # Show a selectbox to choose which entry to delete
                food_to_delete = st.selectbox("Select entry to delete", 
                                             today_food.index.tolist())
                if st.button("Confirm Delete", key="confirm_food"):
                    st.session_state.calorie_log = st.session_state.calorie_log.drop(food_to_delete)
                    st.rerun()
    else:
        st.write("No food entries for today")
    
    # Exercise entries
    st.subheader("Exercise")
    today_exercise = st.session_state.exercise_log[st.session_state.exercise_log['Date'] == selected_date]
    if not today_exercise.empty:
        st.dataframe(today_exercise[['Exercise', 'Minutes', 'CaloriesBurned']])
        st.write(f"**Total Calories Burned: {today_exercise['CaloriesBurned'].sum()}**")
    else:
        st.write("No exercise logged for today")

# Food Database Page
elif page == "Food Database":
    st.title("🥗 Food Database")
    
    # Display current database
    st.subheader("Current Foods")
    edited_df = st.data_editor(st.session_state.food_db, num_rows="dynamic")
    
    if st.button("Save Changes", type="primary"):
        st.session_state.food_db = edited_df
        st.success("Food database updated!")
    
    # Add new food
    st.subheader("Add New Food")
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
    
    with col1:
        new_food = st.text_input("Food Name")
    with col2:
        new_cal_gram = st.number_input("Cal/gram", min_value=0.0, step=0.01)
    with col3:
        new_cal_unit = st.number_input("Cal/unit", min_value=0.0, step=1.0)
    with col4:
        st.write("")
        st.write("")
        if st.button("Add Food"):
            if new_food:
                new_entry = pd.DataFrame({
                    'Food': [new_food],
                    'CaloriesPerGram': [new_cal_gram],
                    'CaloriesPerUnit': [new_cal_unit]
                })
                st.session_state.food_db = pd.concat([st.session_state.food_db, new_entry], ignore_index=True)
                st.success(f"Added {new_food} to database!")
                st.rerun()

# Analytics Page
elif page == "Analytics":
    st.title("📈 Analytics")
    
    # Calorie Trends
    st.header("Calorie Trends")
    
    if not st.session_state.calorie_log.empty or not st.session_state.exercise_log.empty:
        # Prepare data
        daily_calories = st.session_state.calorie_log.groupby('Date')['Calories'].sum().reset_index()
        daily_calories.columns = ['Date', 'CaloriesIn']
        
        daily_exercise = st.session_state.exercise_log.groupby('Date')['CaloriesBurned'].sum().reset_index()
        daily_exercise.columns = ['Date', 'CaloriesOut']
        
        # Merge data
        daily_data = pd.merge(daily_calories, daily_exercise, on='Date', how='outer').fillna(0)
        daily_data['NetCalories'] = daily_data['CaloriesIn'] - daily_data['CaloriesOut']
        daily_data = daily_data.sort_values('Date')
        
        # Create plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily_data['Date'], y=daily_data['CaloriesIn'],
                                mode='lines+markers', name='Calories In',
                                line=dict(color='blue', width=3)))
        fig.add_trace(go.Scatter(x=daily_data['Date'], y=daily_data['CaloriesOut'],
                                mode='lines+markers', name='Calories Burned',
                                line=dict(color='orange', width=3)))
        fig.add_trace(go.Scatter(x=daily_data['Date'], y=daily_data['NetCalories'],
                                mode='lines+markers', name='Net Calories',
                                line=dict(color='green', width=3, dash='dash')))
        
        fig.update_layout(title='Daily Calorie Balance',
                         xaxis_title='Date',
                         yaxis_title='Calories',
                         hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No calorie data available")
    
    # Weight Trends
    st.header("Weight Trends")
    
    if not st.session_state.weight_log.empty:
        weight_data = st.session_state.weight_log.sort_values('Date')
        
        fig = px.line(weight_data, x='Date', y='Weight',
                     markers=True, title='Body Weight Over Time')
        fig.update_traces(line=dict(color='orange', width=3))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No weight data available")
    
    # Summary Statistics
    st.header("Summary Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📊 Calorie Stats")
        if not st.session_state.calorie_log.empty:
            daily_cals = st.session_state.calorie_log.groupby('Date')['Calories'].sum()
            st.metric("Avg Daily Calories", f"{daily_cals.mean():.0f}")
            st.metric("Days Tracked", len(daily_cals))
            st.metric("Total Calories", f"{daily_cals.sum():.0f}")
        else:
            st.write("No data")
    
    with col2:
        st.subheader("🏃 Exercise Stats")
        if not st.session_state.exercise_log.empty:
            daily_ex = st.session_state.exercise_log.groupby('Date').agg({
                'CaloriesBurned': 'sum',
                'Minutes': 'sum'
            })
            st.metric("Avg Daily Burn", f"{daily_ex['CaloriesBurned'].mean():.0f}")
            st.metric("Avg Daily Minutes", f"{daily_ex['Minutes'].mean():.0f}")
            st.metric("Total Burned", f"{daily_ex['CaloriesBurned'].sum():.0f}")
        else:
            st.write("No data")
    
    with col3:
        st.subheader("⚖️ Weight Stats")
        if not st.session_state.weight_log.empty:
            current = st.session_state.weight_log.iloc[-1]['Weight']
            start = st.session_state.weight_log.iloc[0]['Weight']
            st.metric("Current Weight", f"{current:.1f} kg")
            st.metric("Starting Weight", f"{start:.1f} kg")
            st.metric("Weight Change", f"{current - start:+.1f} kg")
        else:
            st.write("No data")

# Export Data Page
elif page == "Export Data":
    st.title("💾 Export Data")
    
    st.write("Download your tracking data as CSV files:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Food log
        if st.button("📥 Download Food Log"):
            csv = st.session_state.calorie_log.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"calorie_log_{date.today()}.csv",
                mime="text/csv"
            )
        
        # Weight log
        if st.button("📥 Download Weight Log"):
            csv = st.session_state.weight_log.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"weight_log_{date.today()}.csv",
                mime="text/csv"
            )
    
    with col2:
        # Exercise log
        if st.button("📥 Download Exercise Log"):
            csv = st.session_state.exercise_log.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"exercise_log_{date.today()}.csv",
                mime="text/csv"
            )
        
        # Notes log
        if st.button("📥 Download Notes"):
            csv = st.session_state.notes_log.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"notes_log_{date.today()}.csv",
                mime="text/csv"
            )
    
    # Download all as ZIP
    st.subheader("Download All Data")
    if st.button("📦 Download All as ZIP"):
        # Create a ZIP file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add each CSV to the ZIP
            zip_file.writestr("calorie_log.csv", st.session_state.calorie_log.to_csv(index=False))
            zip_file.writestr("weight_log.csv", st.session_state.weight_log.to_csv(index=False))
            zip_file.writestr("exercise_log.csv", st.session_state.exercise_log.to_csv(index=False))
            zip_file.writestr("notes_log.csv", st.session_state.notes_log.to_csv(index=False))
            zip_file.writestr("food_database.csv", st.session_state.food_db.to_csv(index=False))
        
        st.download_button(
            label="Download ZIP",
            data=zip_buffer.getvalue(),
            file_name=f"fitness_data_{date.today()}.zip",
            mime="application/zip"
        )

# Footer
st.markdown("---")
st.markdown("🥗 Calorie & Weight Tracker | Made with Streamlit")

# To deploy:
# 1. Save this as app.py
# 2. Create requirements.txt with:
#    streamlit
#    pandas
#    plotly
# 3. Push to GitHub
# 4. Go to share.streamlit.io
# 5. Deploy your app for FREE!