import { useState, useEffect, useCallback, useMemo } from 'react';
import { Play, Pause, X, RotateCcw, Clock, Zap } from 'lucide-react';
import Modal from "./components/Modal";
import Header from './layout/Header';

const INITIAL_WORK_TIME = 25 * 60; // 25 minutes in seconds
const INITIAL_BREAK_TIME = 5 * 60; // 5 minutes in seconds
const API_URL = 'http://localhost:8000/pomodoro';

export default function Home() {

    // recommended by AI models (set by API, used for the next cycle)
    const [currentWorkDuration, setCurrentWorkDuration] = useState(INITIAL_WORK_TIME);
    const [currentBreakDuration, setCurrentBreakDuration] = useState(INITIAL_BREAK_TIME);

    // timer
    const [status, setStatus] = useState('TRABAJO');
    const [timeRemaining, setTimeRemaining] = useState(INITIAL_WORK_TIME);
    const [isActive, setIsActive] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    // time tracking
    const [totalWorkTimeToday, setTotalWorkTimeToday] = useState(0);
    const [totalBreakTimeToday, setTotalBreakTimeToday] = useState(0);

    // modal
    const [showModal1, setShowModal1] = useState(false);
    const [showModal2, setShowModal2] = useState(false);
    const [fatigueLevel, setFatigueLevel] = useState(3);

    // --------------------------------- FUNCTIONS ---------------------------------

    const formatTime = (timeInSeconds) => {
        const minutes = Math.floor(timeInSeconds / 60);
        const seconds = timeInSeconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    };

    // timer start

    const startNextBlock = useCallback((workDuration, breakDuration) => {
        // set opposite status from current
        const nextStatus = status === 'TRABAJO' ? 'DESCANSO' : 'TRABAJO';

        // new recommendations
        const duration = nextStatus === 'TRABAJO' ? workDuration : breakDuration;

        setStatus(nextStatus);
        setTimeRemaining(duration);
        setIsActive(true);
        console.log(`[ACTION] Starting ${nextStatus}: ${duration / 60} minutes.`);
    }, [status]);

    // call backend, update times, start the next block

    const fetchNextTimesAndStart = useCallback(async (
        fatigue,
        // timeShortageAnswer,
        isManualRestart = false
    ) => {

        setShowModal1(false);
        setShowModal2(false);
        setIsLoading(true);

        // 1. Prepare Observation for the RL model
        const observation = {
            fatigue: fatigue,
            work_minutes_day: Math.floor(totalWorkTimeToday / 60),
            break_minutes_day: Math.floor(totalBreakTimeToday / 60),
            // for future time_shortage implementation
            // time_shortage: timeShortageAnswer === 'Sí' ? 1 : 0
        };

        try {
            console.log("[API] Sending Observation:", observation);
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin':'*',
                    'Access-Control-Allow-Methods':'POST,PATCH,OPTIONS'
                 },
                body: JSON.stringify(observation)
            });

            if (!response.ok) throw new Error(`API returned status ${response.status}`);

            const data = await response.json();

            // The API returns minutes, convert to seconds
            const newWorkTime = data.work * 60;
            const newBreakTime = data.break * 60;

            console.log(`[API] Received new times: Work ${data.work}m, Break ${data.break}m`);

            // 2. Update the durations for future cycles
            setCurrentWorkDuration(newWorkTime);
            setCurrentBreakDuration(newBreakTime);

            // 3. Start the next block immediately using the new durations
            startNextBlock(newWorkTime, newBreakTime);

        } catch (error) {
            console.error("Error fetching recommended times. Falling back to default.", error);
            // Fallback: Use initial times if API fails
            setCurrentWorkDuration(INITIAL_WORK_TIME);
            setCurrentBreakDuration(INITIAL_BREAK_TIME);
            startNextBlock(INITIAL_WORK_TIME, INITIAL_BREAK_TIME);
        } finally {
            setIsLoading(false);
        }
    }, [startNextBlock, totalWorkTimeToday, totalBreakTimeToday]);

    // --------------------------------- STATUS HANDLERS ---------------------------------

    const handlePauseToggle = () => {
        setIsActive(prev => !prev);
    };

    const handleSkipBlock = () => {
        setIsActive(false);
        setTimeRemaining(0);
        console.log('[ACTION] Skip button clicked. Time set to 00:00. Timer paused.');
    };

    const handleEndBlock = () => {
        setIsActive(false);
        setShowModal1(true);
        console.log('[ACTION] End button clicked. Timer paused. Open modal.');
    };

    const handleResetToInitial = () => {
        setIsActive(false);
        setStatus('TRABAJO');
        setTimeRemaining(INITIAL_WORK_TIME);
        setCurrentWorkDuration(INITIAL_WORK_TIME);
        setCurrentBreakDuration(INITIAL_BREAK_TIME);
        setTotalWorkTimeToday(0);
        setTotalBreakTimeToday(0);
        setFatigueLevel(3);
        console.log('[ACTION] Reset to initial state.');
    };

    // --------------------------------- MODAL HANDLERS ---------------------------------

    const handleFatigueSubmit = (level) => {
        console.log(`[SUBMIT] Fatigue: Level ${level}.`);
        setShowModal1(false);
        setShowModal2(true);
    };

    const handleTimeShortageSubmit = (answer) => {
        console.log(`[SUBMIT] Time Shortage: ${answer}.`);
        fetchNextTimesAndStart(fatigueLevel, answer);
    };

    // --------------------------------- TIMER EFFECT ---------------------------------
    useEffect(() => {
        let interval = null;

        if (isActive && timeRemaining > 0) {
            interval = setInterval(() => {
                setTimeRemaining(prevTime => prevTime - 1);
            }, 1000);
        } else if (timeRemaining === 0 && isActive) {
            clearInterval(interval);
            setIsActive(false);

            const durationOfCompletedBlock = status === 'TRABAJO' ? currentWorkDuration : currentBreakDuration;

            if (status === 'TRABAJO') {
                setTotalWorkTimeToday(p => p + durationOfCompletedBlock);
            } else {
                setTotalBreakTimeToday(p => p + durationOfCompletedBlock);
            }

            setShowModal1(true);
            console.log(`[TIMER] ${status} time over. Total Work Today: ${Math.floor((totalWorkTimeToday + durationOfCompletedBlock) / 60)}m. Open modal.`);
        }

        return () => clearInterval(interval);
    }, [isActive, timeRemaining, status, currentWorkDuration, currentBreakDuration, totalWorkTimeToday]);

    // --------------------------------- DYNAMIC STATES  ---------------------------------

    const timerText = useMemo(() => formatTime(timeRemaining), [timeRemaining]);
    const isTimeOver = timeRemaining === 0;

    // changes style classes based on status
    const pauseButtonClass = isActive ? 'pause-button-active' : 'pause-button-inactive';

    // calculates slider fill percentage for css animation
    const sliderFillPercent = ((fatigueLevel - 1) / 4) * 100;

    const totalWorkMinutes = Math.floor(totalWorkTimeToday / 60);
    const totalBreakMinutes = Math.floor(totalBreakTimeToday / 60);

    return (
        <div className="app-container">
            <Header />
            <main className="main-content">
                {/* STATUS TEXT */}
                <p className={`status-text`}>
                    {status}
                </p>
                {/* TIME DURATION */}
                {/* <p className='text-gray-400 text-sm mt-2'>
                    Duración: {status === 'TRABAJO' ? Math.floor(currentWorkDuration / 60) : Math.floor(currentBreakDuration / 60)} min
                </p> */}

                {/* TIMER COUNTDOWN */}
                <div className="timer-container">
                    <p className="timer-display">
                        {timerText}
                    </p>

                    {/* PAUSE BUTTON */}
                    <div className="pause-button-wrapper">
                        <button
                            onClick={handlePauseToggle}
                            className={`pause-button ${pauseButtonClass}`}
                            aria-label={isActive ? "Pausar" : "Reanudar"}
                            disabled={isLoading}
                        >
                            {isActive ? <Pause size={40} /> : <Play size={40} />}
                        </button>
                    </div>
                </div>

                {/* TIME TRACKING */}
                <div className="counter-group">
                    <p className="counter-text">
                        Trabajo hoy: {totalWorkMinutes} min
                    </p>
                    <p className="counter-text">
                        Descanso hoy: {totalBreakMinutes} min
                    </p>
                </div>

                {/* END AND SKIP BUTTONS*/}
                <div className="control-buttons-group">
                    <button
                        onClick={handleEndBlock}
                        className="control-button"
                        disabled={isTimeOver || isLoading}
                    >
                        <Clock size={20} /> Terminar bloque
                    </button>

                    <button
                        onClick={handleSkipBlock}
                        className="control-button"
                        disabled={isLoading}
                    >
                        <Zap size={20} /> Saltar bloque
                    </button>
                </div>

                {/* RESTART BUTTON */}
                <div className="restart-group">
                    {/* <span> */}
                    <div className="restart-button-group">
                        <button
                            onClick={() => fetchNextTimesAndStart(fatigueLevel, 'No', true)}
                            className="restart-button"
                            disabled={isLoading}
                        >
                            <Clock size={40} />
                        </button>
                        Generar siguiente
                        <br />
                        pomodoro
                    </div>
                    <br />
                    <span>
                        <div className="restart-button-group">
                            <button
                                onClick={handleResetToInitial}
                                className="restart-button"
                                disabled={isLoading}
                            >
                                <RotateCcw size={40} className="mb-1" />

                            </button>
                            Reiniciar
                            <br />
                            contadores
                        </div>
                    </span>
                </div>
            </main>

            {/* --- Modals --- */}

            {/* --- MODAL 1: fatigue level with slider --- */}
            <Modal
                title="¿Qué tan cansado te sientes?"
                isOpen={showModal1}
            >
                <div className="slider-container">
                    {/* css does the maths from the parameters */}
                    <input
                        type="range"
                        min="1"
                        max="5"
                        step="1"
                        value={fatigueLevel}
                        onChange={(e) => setFatigueLevel(parseInt(e.target.value))}
                        onMouseUp={() => handleFatigueSubmit(fatigueLevel)} // mouse submission
                        onTouchEnd={() => handleFatigueSubmit(fatigueLevel)} // touch submission
                        className="slider-input"
                        style={{ '--slider-value': `${sliderFillPercent}%` }}
                    />
                    {/* percentage from calc */}
                    <div
                        className="slider-value-bubble"
                        style={{ left: `${sliderFillPercent}%` }}
                    >
                        {fatigueLevel}
                    </div>
                </div>
            </Modal>

            {/* --- MODAL 2: time shortage (Y/N) --- */}
            <Modal
                title="¿Te faltó tiempo?"
                isOpen={showModal2}
            >
                <div className="modal-footer">
                    <button
                        onClick={() => handleTimeShortageSubmit('Sí')}
                        className="modal-action-button modal-primary-button"
                    >
                        Sí
                    </button>
                    <button
                        onClick={() => handleTimeShortageSubmit('No')}
                        className="modal-action-button modal-secondary-button"
                    >
                        No
                    </button>
                </div>
            </Modal>

        </div>
    );

}