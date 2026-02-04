import datetime as dt
import json
import streamlit as st
import streamlit.components.v1 as components
from streamlit_lottie import st_lottie
import requests as rq
import os

st.set_page_config(page_title="My To Do List", page_icon="✅")

# --- [1. DATA LAYER] 데이터 저장 및 로드 관련 함수 ---
def load_data(path='data.json'):
    if not os.path.exists(path):
        save_data([], path)
        return []
    try:
        if os.path.getsize(path)==0:
            return []
        with open(path, 'r', encoding='UTF-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
            st.warning(f"'{path}' 파일이 비어있거나 형식이 잘못되어 초기화합니다.")
            return []

def save_data(items, path='data.json'):
    with open(path, 'w', encoding='UTF-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=4)

def load_lottie(url):
    try:
        r = rq.get(url)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# --- [2. UI COMPONENT LAYER] 화면에 그려지는 요소들 ---
def render_header():
    """상단 로고와 제목 렌더링"""
    col1, col2 = st.columns([1, 2])
    with col1:
        lottie_json = load_lottie('https://assets8.lottiefiles.com/packages/lf20_fWd36IjnsR.json')
        if lottie_json:
            st_lottie(lottie_json, speed=2, width=150)
    with col2:
        st.markdown("<h1 style='padding-top:20px;'>My To Do List</h1>", unsafe_allow_html=True)

def render_add_form():
    """새로운 할 일 추가 폼"""
    with st.expander("➕ 새로운 할 일 추가하기"):
        with st.form(key='quick_add', clear_on_submit=True):
            desc = st.text_input("무엇을 해야 하나요?")
            c1, c2 = st.columns(2)
            date = c1.date_input("날짜", value=dt.datetime.now())
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
    """개별 할 일 항목 렌더링"""
    with st.container():

        #날짜 확인
        today = dt.datetime.now().date()
        item_date = dt.datetime.strptime(item['date'], '%Y-%m-%d').date()
        
        is_today = (item_date == today) and (item['status'] != 'Done')
        is_overdue = (item_date < today) and (item['status'] != 'Done') 

        with st.container():
            if is_overdue:
                st.markdown("<span style='color: #ffffff; font-size: 0.8rem;'>⌛ 기한이 지났습니다</span>", unsafe_allow_html=True)
            elif is_today:
                st.markdown("<span style='color: #ff4b4b; font-size: 0.8rem;'>🔥 기한이 오늘입니다</span>", unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns([0.5, 4, 1])
            # 1. 상태 토글 (체크박스)
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

            # 2. 내용 표시
            with c2:
                description = item['description']
                
                if item['status'] == 'Done':
                    # 완료: 취소선 + 회색
                    st.markdown(f"<span style='color: #888888;'>~~{description}~~</span>", unsafe_allow_html=True)
                    st.caption(f"📅 {item['date']} | 완료됨")
                
                elif is_overdue:
                    # 기한 경과: 진한 회색 + 연체 아이콘
                    st.markdown(f"<span style='color: #cccccc;'>🚫 {description}</span>", unsafe_allow_html=True)
                    st.caption(f"📅 {item['date']} (기한 지남) | ⏰ {item['time']}")
                
                elif is_today:
                    # 오늘 마감: 빨간색 강조
                    st.markdown(f"<span style='color: #ff4b4b; font-weight: bold;'>🔥 {description}</span>", unsafe_allow_html=True)
                    st.caption(f"📅 오늘까지 | ⏰ {item['time']}")
                
                else:
                    # 일반 대기 중
                    st.markdown(f"**{description}**")
                    st.caption(f"📅 {item['date']} | ⏰ {item['time']}")


            # 3. 삭제 버튼
            with c3:
                if st.button("🗑️", key=f"del_{filter_name}_{index}"):
                    st.session_state['items'].pop(index)
                    save_data(st.session_state['items'])
                    st.rerun()
        st.write("---")

def render_stats():
    """하단 통계 및 프로그레스 바"""
    items = st.session_state['items']
    if not items:
        return
    done_count = len([x for x in items if x['status'] == 'Done'])
    progress = done_count / len(items)
    st.progress(progress)
    st.write(f"📊 전체 {len(items)}개 중 {done_count}개 완료! ({int(progress*100)}%)")

# --- [3. MAIN LOGIC LAYER] 앱 실행 흐름 제어 ---
def main():
    # 세션 상태 초기화
    if 'items' not in st.session_state:
        st.session_state['items'] = load_data()

    # 상단부
    render_header()
    render_add_form()

    # 메인 리스트 (탭 구성)
    t1, t2, t3 = st.tabs(['All', 'Pending', 'Done'])
    tab_info = [
        (t1, None, "모든 할 일"),
        (t2, "Pending", "진행 중"),
        (t3, "Done", "완료됨")
    ]

    for tab, filter_status, label in tab_info:
        with tab:
            st.subheader(label)
            # 필터링된 항목만 추출하되, 원본 인덱스를 유지
            for i, item in enumerate(st.session_state['items']):
                if filter_status is None or item['status'] == filter_status:
                    render_todo_item(i, item, filter_name=str(filter_status))
            
            # 항목이 없을 때 예외 처리
            visible = [x for x in st.session_state['items'] if filter_status is None or x['status'] == filter_status]
            if not visible:
                st.info(f"{label} 목록이 비어 있습니다.")

    # 하단 통계
    render_stats()

if __name__ == "__main__":
    main()