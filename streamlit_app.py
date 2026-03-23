import streamlit as st

st.set_page_config(page_title = 'IST 488 Homeworks',
                  initial_sidebar_state = 'expanded')

st.title('IST 488 Homeworks')
Homework1 = st.Page('homeworks/hw1.py', title = 'Homework 1', icon = '🧑‍🎓')
Homework2 = st.Page('homeworks/hw2.py', title = 'Homework 2', icon = '🧑‍🎓')
Homework3 = st.Page('homeworks/hw3.py', title = 'Homework 3', icon = '🧑‍🎓')
Homework4 = st.Page('homeworks/hw4.py', title = 'Homework 4', icon = '🧑‍🎓')
Homework7 = st.Page('homeworks/hw7.py', title = 'Homework7', icon = '🧑‍🎓')
pg = st.navigation([Homework1, Homework2, Homework3, Homework4, Homework7])

pg.run()