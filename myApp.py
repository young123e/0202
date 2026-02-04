import datetime as dt
import json
import streamlit as st
import streamlit.components.v1 as components
from streamlit_lottie import st_lottie
import requests as rq
import os

st.set_page_config(page_title="My To Do List", page_icon="✅")

# --- [1. DATA LAYER] ---
def load_data(path='data.json'):
    if not os.path.exists(path):
        save_data([], path)
        return []
    try:
        if os.path.getsize(path) == 0: return []
        with open(path, 'r', encoding='UTF-8') as f:
            items = json.load(f)
            # [추가] 로드 시 날짜/시간 순으로 정렬
            items.sort(key=lambda x: (x['date'], x['time']))
            return items
    except (json.JSONDecodeError, ValueError):
        st.warning(f"'{path}' 파일이 비어있거나 형식이 잘못되어 초기화합니다.")
        return []

def save_data(items, path='data.json'):
    # [추가] 저장 전 항상 정렬 (날짜 -> 시간 순)
    items.sort(key=lambda x: (x['date'], x['time']))
    with open(path, 'w', encoding='UTF-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=4)

def load_lottie(url):
    try:
        r = rq.get(url)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- [2. UI COMPONENT LAYER] ---
def render_header():
    col1, col2 = st.columns([1, 2])
    with col1:
        lottie_json = load_lottie('https://assets8.lottiefiles.com/packages/lf20_fWd36IjnsR.json')
        if lottie_json: st_lottie(lottie_json, speed=2, width=150)
    with col2:
        st.markdown("<h1 style='padding-top:20px;'>My To Do List</h1>", unsafe_allow_html=True)

def render_add_form():
    with st.expander("➕ 새로운 할 일 추가하기"):
        with st.form(key='quick_add', clear_on_submit=True):
            desc = st.text_input("무엇을 해야 하나요?")
            c1, c2 = st.columns(2)
            date = c1.date_input("기한", value=dt.datetime.now())
            time = c2.time_input("시간", value=dt.datetime.now().time())
            if st.form_submit_button("추가하기") and desc:
                new_item = {
                    'description': desc,
                    'date': str(date),
                    'time': time.strftime('%H:%M:%S'),
                    'status': 'Pending'
                }
                st.session_state['items'].append(new_item)
                save_data(st.session_state['items'])
                st.rerun()

def render_todo_item(index, item, filter_name):
    """개별 할 일 항목 렌더링 (수정 기능 포함)"""
    today = dt.datetime.now().date()
    item_date = dt.datetime.strptime(item['date'], '%Y-%m-%d').date()
    is_today = (item_date == today) and (item['status'] != 'Done')
    is_overdue = (item_date < today) and (item['status'] != 'Done')

    # 수정 모드 확인
    edit_key = f"editing_{index}"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = False

    with st.container():
        # --- 수정 모드일 때 ---
        if st.session_state[edit_key]:
            with st.form(key=f"edit_form_{filter_name}_{index}"):
                edit_desc = st.text_input("할 일 수정", value=item['description'])
                e_c1, e_c2 = st.columns(2)
                edit_date = e_c1.date_input("기한", value=item_date)
                edit_time = e_c2.time_input("시간", value=dt.datetime.strptime(item['time'], '%H:%M:%S').time())
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 저장"):
                    st.session_state['items'][index].update({
                        'description': edit_desc,
                        'date': str(edit_date),
                        'time': edit_time.strftime('%H:%M:%S')
                    })
                    save_data(st.session_state['items'])
                    st.session_state[edit_key] = False
                    st.rerun()
                if b2.form_submit_button("❌ 취소"):
                    st.session_state[edit_key] = False
                    st.rerun()
        
        # --- 일반 표시 모드일 때 ---
        else:
            if is_overdue:
                st.markdown("<span style='color: #ffffff; font-size: 0.8rem;'>⌛ 기한이 지났습니다</span>", unsafe_allow_html=True)
            elif is_today:
                st.markdown("<span style='color: #ff4b4b; font-size: 0.8rem;'>🔥 기한이 오늘입니다</span>", unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns([0.5, 4, 1.2]) # 버튼 공간 확보를 위해 비율 조정
            
            with c1:
                is_done = (item['status'] == 'Done')
                if st.checkbox("", value=is_done, key=f"cb_{filter_name}_{index}"):
                    new_status = 'Done'
                else:
                    new_status = 'Pending'
                
                if new_status != item['status']:
                    st.session_state['items'][index]['status'] = new_status
                    save_data(st.session_state['items'])
                    st.rerun()

            with c2:
                description = item['description']
                if item['status'] == 'Done':
                    st.markdown(f"<span style='color: #888888;'>~~{description}~~</span>", unsafe_allow_html=True)
                    st.caption(f"📅 {item['date']} | 완료됨")
                elif is_overdue:
                    st.markdown(f"<span style='color: #cccccc;'>🚫 {description}</span>", unsafe_allow_html=True)
                    st.caption(f"📅 {item['date']} (기한 지남) | ⏰ {item['time']}")
                elif is_today:
                    st.markdown(f"<span style='color: #ff4b4b; font-weight: bold;'>🔥 {description}</span>", unsafe_allow_html=True)
                    st.caption(f"📅 오늘까지 | ⏰ {item['time']}")
                else:
                    st.markdown(f"**{description}**")
                    st.caption(f"📅 {item['date']} | ⏰ {item['time']}")

            with c3:
                btn_c1, btn_c2 = st.columns(2)
                if btn_c1.button("📝", key=f"ed_btn_{filter_name}_{index}"):
                    st.session_state[edit_key] = True
                    st.rerun()
                if btn_c2.button("🗑️", key=f"del_{filter_name}_{index}"):
                    st.session_state['items'].pop(index)
                    save_data(st.session_state['items'])
                    st.rerun()
        st.write("---")

def render_stats():
    items = st.session_state['items']
    if not items: return
    done_count = len([x for x in items if x['status'] == 'Done'])
    progress = done_count / len(items)
    st.progress(progress)
    st.write(f"📊 전체 {len(items)}개 중 {done_count}개 완료! ({int(progress*100)}%)")

# --- [3. MAIN LOGIC LAYER] ---
def main():
    if 'items' not in st.session_state:
        st.session_state['items'] = load_data()

    render_header()
    render_add_form()

    t1, t2, t3 = st.tabs(['All', 'Pending', 'Done'])
    tab_info = [(t1, None, "모든 할 일"), (t2, "Pending", "진행 중"), (t3, "Done", "완료됨")]

    for tab, filter_status, label in tab_info:
        with tab:
            st.subheader(label)
            # 필터링 및 렌더링
            has_visible = False
            for i, item in enumerate(st.session_state['items']):
                if filter_status is None or item['status'] == filter_status:
                    render_todo_item(i, item, filter_name=str(filter_status))
                    has_visible = True
            if not has_visible:
                st.info(f"{label} 목록이 비어 있습니다.")

    render_stats()

if __name__ == "__main__":
    main()