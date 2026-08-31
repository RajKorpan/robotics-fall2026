from __future__ import annotations
from lab.session import response,set_response
def text_response(st,key,label,*,height=100):
    value=st.text_area(label,value=str(response(st,key,"")),height=height,key=f"widget.{key}"); set_response(st,key,value); return value
def render_check(st,check):
    st.dataframe([{"Requirement":x.label,"Actual":x.actual,"Expected":x.expected,"Status":"Pass" if x.passed else "Not yet"} for x in check.requirements],hide_index=True,width="stretch"); (st.success if check.passed else st.warning)(check.summary if check.passed else "The mission is not complete yet.")

