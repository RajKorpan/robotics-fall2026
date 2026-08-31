from lab.navigation import set_stage
def render(st):
    st.header("From concern to requirement to test")
    st.table([
      {"Concern":"Privacy","Engineering form":"data fields, processing location, retention, access, consent, deletion","Evidence":"lifecycle trace + requirement checks"},
      {"Concern":"Fairness","Engineering form":"subgroup metrics, sensing/data intervention, abstention, review","Evidence":"TPR/FPR, disparity, coverage, workload"},
      {"Concern":"Safety","Engineering form":"speed/distance bounds, stop path, confidence and fallback","Evidence":"scenario pass/fail"},
      {"Concern":"Accessibility","Engineering form":"redundant feedback and control modalities","Evidence":"tasks remain possible without one modality"},
      {"Concern":"Human control","Engineering form":"confirmation, override, stop, escalation authority","Evidence":"consequential and failure scenarios"},
    ])
    st.warning("Passing a specified test suite is bounded evidence. It does not prove universal fairness, privacy, accessibility, or safety.")
    if st.button("Continue"): set_stage(st,"background")

