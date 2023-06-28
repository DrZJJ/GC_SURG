import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from pysurvival.utils import load_model

st.set_page_config(layout="wide")

@st.cache(show_spinner=False)
def load_setting():
    settings = {
        'Age': {'values': ["20-69", "70+"], 'type': 'selectbox', 'init_value': 0, 'add_after': ', year'},
        'Sex': {'values': ["Male", "Female"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Marital status': {'values': ["Married", "Unmarried"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Race recode': {'values': ["American Indian/Alaska Native", "Asian or Pacific Islander", "Black", "White"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Primary Site': {'values': ["C16.0", "C16.1", "C16.2", "C16.3", "C16.4", "C16.5", "C16.6", "C16.8", "C16.9"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Grade': {'values': ["Well differentiated or Moderately differentiated", "Poorly differentiated or Undifferentiated"],
             'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Summary stage': {'values': ["Distant", "Localized", "Regional"],
             'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'T stage': {'values': ["T1", "T2","T3","T4"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'N stage': {'values': ["N0", "N1","N2","N3"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'M stage': {'values': ["M0", "M1"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'AJCC stage': {'values': ["I", "II", "III", "IV"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Radiation': {'values': ["Yes", "No"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Chemotherapy recode': {'values': ["Yes", "No"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Tumor size': {'values': ["< 5", "5 +"], 'type': 'selectbox', 'init_value': 0, 'add_after': ', cm'},
        'Regional nodes examined ': {'values': [0, 150], 'type': 'slider', 'init_value': 75, 'add_after': ''},
        'Regional nodes positive ': {'values': [0, 100], 'type': 'slider', 'init_value': 50, 'add_after': ''},
        'Lymph node metastasis rate': {'values': ["0", "<30", "30-70", ">70"], 'type': 'selectbox',
                               'init_value': 0,
                               'add_after': '%'},
        
    }
    input_keys = ['Age', 'Sex', 'Marital status', 'Race recode', 'Primary Site',
       'Grade', 'Summary stage', 'T stage', 'N stage', 'M stage', 'AJCC stage', 'Radiation', 'Chemotherapy recode', 'Tumor size', 'Regional nodes examined ','Regional nodes positive ', 'Lymph node metastasis rate']
    return settings, input_keys


settings, input_keys = load_setting()


@st.cache_data(show_spinner=False)
def get_model(name='DeepSurv'):
    model = load_model('{}.zip'.format(name))
    return model


def get_code():
    sidebar_code = []
    for key in settings:
        if settings[key]['type'] == 'slider':
            sidebar_code.append(
                "{} = st.slider('{}',{},{},key='{}')".format(
                    key.replace(' ', '____'),
                    key + settings[key]['add_after'],
                    # settings[key]['values'][0],
                    ','.join(['{}'.format(value) for value in settings[key]['values']]),
                    settings[key]['init_value'],
                    key
                )
            )
        if settings[key]['type'] == 'selectbox':
            sidebar_code.append('{} = st.selectbox("{}",({}),{},key="{}")'.format(
                key.replace(' ', '____'),
                key + settings[key]['add_after'],
                ','.join('"{}"'.format(value) for value in settings[key]['values']),
                settings[key]['init_value'],
                key
            )
            )
    return sidebar_code




# print('\n'.join(sidebar_code))
if 'patients' not in st.session_state:
    st.session_state['patients'] = []
if 'display' not in st.session_state:
    st.session_state['display'] = 1
if 'model' not in st.session_state:
    st.session_state['model'] = 'deepsurv'
deepsurv_model = get_model(st.session_state['model'])
sidebar_code = get_code()
def plot_survival():
    pd_data = pd.concat(
        [
            pd.DataFrame(
                {
                    'Survival': item['survival'],
                    'Time': item['times'],
                    'Patients': [item['No'] for i in item['times']]
                }
            ) for item in st.session_state['patients']
        ]
    )
    if st.session_state['display']:
        fig = px.line(pd_data, x="Time", y="Survival", color='Patients', range_y=[0, 1])
    else:
        fig = px.line(pd_data.loc[pd_data['Patients'] == pd_data['Patients'].to_list()[-1], :], x="Time", y="Survival",
                      range_y=[0, 1])
    fig.update_layout(template='simple_white',
                      title={
                          'text': 'Estimated Survival Probability',
                          'y': 0.9,
                          'x': 0.5,
                          'xanchor': 'center',
                          'yanchor': 'top',
                          'font': dict(
                              size=25
                          )
                      },
                      plot_bgcolor="white",
                      xaxis_title="Time, month",
                      yaxis_title="Survival probability",
                      )
    st.plotly_chart(fig, use_container_width=True)


def plot_patients():
    patients = pd.concat(
        [
            pd.DataFrame(
                dict(
                    {
                        'Patients': [item['No']],
                        '1-Year': ["{:.2f}%".format(item['1-year'] * 100)],
                        '3-Year': ["{:.2f}%".format(item['3-year'] * 100)],
                        '5-Year': ["{:.2f}%".format(item['5-year'] * 100)]
                    },
                    **item['arg']
                )
            ) for item in st.session_state['patients']
        ]
    ).reset_index(drop=True)
    st.dataframe(patients)

# @st.cache(show_spinner=True)
def predict():
    print('update patients . ##########')
    print(st.session_state)
    input = []
    for key in input_keys:
        value = st.session_state[key]
        if isinstance(value, int):
            input.append(value)
        if isinstance(value, str):
            input.append(settings[key]['values'].index(value))
    survival = deepsurv_model.predict_survival(np.array(input), t=None)
    data = {
        'survival': survival.flatten(),
        'times': [i for i in range(0, len(survival.flatten()))],
        'No': len(st.session_state['patients']) + 1,
        'arg': {key:st.session_state[key] for key in input_keys},
        '1-year': survival[0, 12],
        '3-year': survival[0, 36],
        '5-year': survival[0, 60]
    }
    st.session_state['patients'].append(
        data
    )
    print('update patients ... ##########')

def plot_below_header():
    col1, col2 = st.columns([1, 9])
    col3, col4, col5, col6, col7 = st.columns([2, 2, 2, 2, 2])
    with col1:
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        # st.session_state['display'] = ['Single', 'Multiple'].index(
        #     st.radio("Display", ('Single', 'Multiple'), st.session_state['display']))
        st.session_state['display'] = ['Single', 'Multiple'].index(
            st.radio("Display", ('Single', 'Multiple'), st.session_state['display']))
        # st.radio("Model", ('DeepSurv', 'NMTLR','RSF','CoxPH'), 0,key='model',on_change=predict())
    with col2:
        plot_survival()
    with col4:
        st.metric(
            label='1-Year survival probability',
            value="{:.2f}%".format(st.session_state['patients'][-1]['1-year'] * 100)
        )
    with col5:
        st.metric(
            label='3-Year survival probability',
            value="{:.2f}%".format(st.session_state['patients'][-1]['3-year'] * 100)
        )
    with col6:
        st.metric(
            label='5-Year survival probability',
            value="{:.2f}%".format(st.session_state['patients'][-1]['5-year'] * 100)
        )
    st.write('')
    st.write('')
    st.write('')
    plot_patients()
    st.write('')
    st.write('')
    st.write('')
    st.write('')
    st.write('')

st.header('DeepSurv-based model for predicting survival of Gastric adenocarcinoma', anchor='survival-of-Gastric adenocarcinoma')
if st.session_state['patients']:
    plot_below_header()
st.subheader("Instructions:")
st.write("1. Select patient's infomation on the left\n2. Press predict button\n3. The model will generate predictions")
st.write('***Note: this model is still a research subject, and the accuracy of the results cannot be guaranteed!***')
st.write("***[Paper link](https://pubmed.ncbi.nlm.nih.gov/)(To be updated)***")
with st.sidebar:
    with st.form("my_form",clear_on_submit = False):
        for code in sidebar_code:
            exec(code)
        col8, col9, col10 = st.columns([3, 4, 3])
        with col9:
            prediction = st.form_submit_button(
                'Predict',
                on_click=predict,
                # args=[{key: eval(key.replace(' ', '____')) for key in input_keys}]
            )

