import streamlit as st

st.set_page_config(page_title = 'IST 488 Labs',
                  initial_sidebar_state = 'expanded')

st.title('IST 488 Labs')
Homework1 = st.Page('homeworks/hw1.py', title = 'Homework 1', icon = '🧑‍🎓')
Homework2 = st.Page('homeworks/hw2.py', title = 'Homework 2', icon = '🧑‍🎓')
Homework3 = st.page('homeworks/hw3.py', title = 'Homework 3', icon = '🧑‍🎓')
pg = st.navigation([Homework1, Homework2, Homework3])

pg.run()