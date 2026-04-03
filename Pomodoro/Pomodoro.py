import streamlit as st
import streamlit.components.v1 as components
import time
import random

# Page config
st.set_page_config(page_title="Pomodoro Timer", page_icon="🍅", layout="centered")

# Initialize session state
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'current_task_index' not in st.session_state:
    st.session_state.current_task_index = 0
if 'timer_running' not in st.session_state:
    st.session_state.timer_running = False
if 'timer_type' not in st.session_state:
    st.session_state.timer_type = 'study'  # 'study' or 'break'
if 'time_remaining' not in st.session_state:
    st.session_state.time_remaining = 25 * 60  # 25 minutes in seconds
if 'completed_tasks' not in st.session_state:
    st.session_state.completed_tasks = []
if 'incomplete_tasks' not in st.session_state:
    st.session_state.incomplete_tasks = []
if 'show_reward' not in st.session_state:
    st.session_state.show_reward = False
if 'pomodoros_completed' not in st.session_state:
    st.session_state.pomodoros_completed = 0
if 'awaiting_progress_input' not in st.session_state:
    st.session_state.awaiting_progress_input = False
if 'last_progress_value' not in st.session_state:
    st.session_state.last_progress_value = 0

# Constants
STUDY_TIME = 25 * 60  # 25 minutes
BREAK_TIME = 5 * 60   # 5 minutes
EARLY_COMPLETION_BONUS = 2 * 60  # 2 minutes early = reward

# Rewards list
REWARDS = [
    "🎉 Amazing! You're on fire! Take a victory stretch!",
    "⭐ Superstar! You completed that super fast!",
    "🏆 Champion! Treat yourself to a small snack!",
    "🚀 Rocket speed! You're crushing it today!",
    "💎 Brilliant work! Take a moment to appreciate yourself!",
    "🌟 Stellar performance! You've earned a quick walk!",
]

# Encouragement messages
ENCOURAGEMENTS = [
    "💪 You've got this! Let's tackle it again!",
    "🌱 Progress, not perfection! Keep going!",
    "🔥 Almost there! This session will be the one!",
    "💫 Every expert was once a beginner. Keep pushing!",
    "🎯 Focus mode: activated! You can do it!",
]

def format_time(seconds):
    """Format seconds into MM:SS"""
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"

def get_random_reward():
    return random.choice(REWARDS)

def get_random_encouragement():
    return random.choice(ENCOURAGEMENTS)

def play_notification_sound():
    """Play a short notification beep in the browser."""
    components.html(
        """
        <script>
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (AudioContextClass) {
            const audioCtx = new AudioContextClass();
            const durations = [0.15, 0.15, 0.25];
            const freqs = [880, 988, 1319];

            let startTime = audioCtx.currentTime;

            freqs.forEach((freq, i) => {
                const oscillator = audioCtx.createOscillator();
                const gainNode = audioCtx.createGain();

                oscillator.type = "sine";
                oscillator.frequency.setValueAtTime(freq, startTime);

                gainNode.gain.setValueAtTime(0.0001, startTime);
                gainNode.gain.exponentialRampToValueAtTime(0.2, startTime + 0.01);
                gainNode.gain.exponentialRampToValueAtTime(0.0001, startTime + durations[i]);

                oscillator.connect(gainNode);
                gainNode.connect(audioCtx.destination);

                oscillator.start(startTime);
                oscillator.stop(startTime + durations[i]);

                startTime += durations[i] + 0.05;
            });
        }
        </script>
        """,
        height=0,
    )

def move_to_break():
    """Switch to break mode."""
    st.session_state.timer_type = 'break'
    st.session_state.time_remaining = BREAK_TIME
    st.session_state.timer_running = False
    st.session_state.awaiting_progress_input = False

def move_to_study():
    """Switch to study mode."""
    st.session_state.timer_type = 'study'
    st.session_state.time_remaining = STUDY_TIME
    st.session_state.timer_running = False
    st.session_state.awaiting_progress_input = False

# Title
st.title("🍅 Pomodoro Study Timer")

# Sidebar for task management
with st.sidebar:
    st.header("📝 Task Management")
    
    # Add new task
    new_task = st.text_input("Add a new task:", placeholder="Enter task description...")
    if st.button("➕ Add Task", use_container_width=True):
        if new_task.strip():
            st.session_state.tasks.append({
                'name': new_task.strip(),
                'completed': False,
                'carried_over': False,
                'progress': 0
            })
            st.rerun()
    
    st.divider()
    
    # Display task queue
    st.subheader("📋 Task Queue")
    if st.session_state.tasks:
        for i, task in enumerate(st.session_state.tasks):
            col1, col2 = st.columns([4, 1])
            with col1:
                status = "✅" if task['completed'] else "⏳" if task.get('carried_over') else "📌"
                progress_text = f" ({task.get('progress', 0)}%)" if task.get('progress', 0) > 0 and not task['completed'] else ""
                st.write(f"{status} {task['name']}{progress_text}")
            with col2:
                if st.button("🗑️", key=f"del_{i}"):
                    st.session_state.tasks.pop(i)
                    if st.session_state.current_task_index >= len(st.session_state.tasks):
                        st.session_state.current_task_index = max(0, len(st.session_state.tasks) - 1)
                    st.rerun()
    else:
        st.info("No tasks yet. Add some tasks to get started!")
    
    st.divider()
    
    # Stats
    st.subheader("📊 Session Stats")
    st.metric("Pomodoros Completed", st.session_state.pomodoros_completed)
    st.metric("Tasks Completed", len(st.session_state.completed_tasks))

# Main timer area
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # Current task display
    if st.session_state.tasks and st.session_state.current_task_index < len(st.session_state.tasks):
        current_task = st.session_state.tasks[st.session_state.current_task_index]
        
        if st.session_state.timer_type == 'study':
            st.subheader("📚 Current Task:")
            if current_task.get('carried_over'):
                st.warning(f"**{current_task['name']}**")
                st.caption(get_random_encouragement())
                if current_task.get('progress', 0) > 0:
                    st.caption(f"Previous progress: {current_task['progress']}%")
            else:
                st.info(f"**{current_task['name']}**")
        else:
            st.subheader("☕ Break Time!")
            st.success("Relax and recharge!")
    else:
        if st.session_state.timer_type == 'study':
            st.subheader("📚 Study Session")
            st.caption("Add tasks in the sidebar to track your work!")
        else:
            st.subheader("☕ Break Time!")
            st.success("Relax and recharge!")
    
    st.divider()
    
    # Timer display
    timer_color = "#ff6347" if st.session_state.timer_type == 'study' else "#4CAF50"
    st.markdown(
        f"""
        <div style='text-align: center; padding: 20px;'>
            <h1 style='font-size: 80px; color: {timer_color}; margin: 0;'>
                {format_time(st.session_state.time_remaining)}
            </h1>
            <p style='font-size: 20px; color: gray;'>
                {'🍅 Study Time' if st.session_state.timer_type == 'study' else '🌿 Break Time'}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Show reward if earned
    if st.session_state.show_reward:
        st.balloons()
        st.success(get_random_reward())
        st.session_state.show_reward = False
    
    # Progress question after timer ends
    if st.session_state.awaiting_progress_input:
        st.divider()
        st.subheader("📈 Session Check-in")
        st.write("How far did you get with your task?")
        
        progress_value = st.slider(
            "Task progress",
            min_value=0,
            max_value=100,
            value=st.session_state.last_progress_value,
            step=5
        )
        
        if st.button("Submit progress", use_container_width=True, type="primary"):
            st.session_state.last_progress_value = progress_value
            
            if st.session_state.tasks and st.session_state.current_task_index < len(st.session_state.tasks):
                current_task = st.session_state.tasks[st.session_state.current_task_index]
                current_task['progress'] = progress_value
                
                if progress_value >= 100:
                    current_task['completed'] = True
                    st.session_state.completed_tasks.append(current_task['name'])
                    st.session_state.tasks.pop(st.session_state.current_task_index)
                    if st.session_state.current_task_index >= len(st.session_state.tasks):
                        st.session_state.current_task_index = 0
                    st.success("Nice — task completed!")
                else:
                    current_task['carried_over'] = True
                    if current_task['name'] not in st.session_state.incomplete_tasks:
                        st.session_state.incomplete_tasks.append(current_task['name'])
                    st.info(f"Progress saved: {progress_value}%. You'll continue this task next session.")
            
            move_to_break()
            st.toast("⏰ Study session complete! Time for a break!", icon="☕")
            st.rerun()
    
    st.divider()
    
    # Control buttons
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    with btn_col1:
        start_pause_disabled = st.session_state.awaiting_progress_input
        if st.button(
            "▶️ Start" if not st.session_state.timer_running else "⏸️ Pause",
            use_container_width=True,
            type="primary",
            disabled=start_pause_disabled
        ):
            st.session_state.timer_running = not st.session_state.timer_running
            st.rerun()
    
    with btn_col2:
        reset_disabled = st.session_state.awaiting_progress_input
        if st.button("🔄 Reset", use_container_width=True, disabled=reset_disabled):
            st.session_state.time_remaining = STUDY_TIME if st.session_state.timer_type == 'study' else BREAK_TIME
            st.session_state.timer_running = False
            st.rerun()
    
    with btn_col3:
        if st.session_state.timer_type == 'study':
            complete_disabled = st.session_state.awaiting_progress_input
            if st.button("✅ Complete", use_container_width=True, disabled=complete_disabled):
                if st.session_state.time_remaining >= EARLY_COMPLETION_BONUS:
                    st.session_state.show_reward = True
                
                play_notification_sound()
                
                if st.session_state.tasks and st.session_state.current_task_index < len(st.session_state.tasks):
                    completed_task = st.session_state.tasks[st.session_state.current_task_index]
                    completed_task['completed'] = True
                    completed_task['progress'] = 100
                    st.session_state.completed_tasks.append(completed_task['name'])
                    st.session_state.tasks.pop(st.session_state.current_task_index)
                    if st.session_state.current_task_index >= len(st.session_state.tasks):
                        st.session_state.current_task_index = 0
                
                st.session_state.pomodoros_completed += 1
                move_to_break()
                st.rerun()
        else:
            if st.button("⏭️ Skip Break", use_container_width=True):
                move_to_study()
                st.rerun()

# Timer logic
if st.session_state.timer_running and not st.session_state.awaiting_progress_input:
    time.sleep(1)
    st.session_state.time_remaining -= 1
    
    if st.session_state.time_remaining <= 0:
        st.session_state.timer_running = False
        play_notification_sound()
        
        if st.session_state.timer_type == 'study':
            st.session_state.pomodoros_completed += 1
            st.session_state.time_remaining = 0
            st.session_state.awaiting_progress_input = True
        else:
            move_to_study()
            st.toast("⏰ Break's over! Ready to focus!", icon="🍅")
    
    st.rerun()

# Footer with instructions
st.divider()
with st.expander("ℹ️ How to use"):
    st.markdown("""
    1. **Add tasks** in the sidebar to track what you'll work on  
    2. **Start the timer** to begin a 25-minute study session  
    3. When the study timer ends, **log your progress** with the slider  
    4. **100% = completed**, anything below that carries over to the next session  
    5. **Take breaks** - 5-minute breaks help you stay fresh  
    6. **Track progress** in the sidebar stats  
    """)