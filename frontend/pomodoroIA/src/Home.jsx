import { useState, useEffect, useCallback, useMemo } from 'react';
import { Play, Pause, X, RotateCcw, Clock, Zap } from 'lucide-react';
import Modal from "./components/Modal";
import Header from './layout/Header';

const WORK_TIME = 25 * 60; // 25 minutes in seconds
const BREAK_TIME = 5 * 60; // 5 minutes in seconds
const INITIAL_TIME = WORK_TIME;

export default function Home() {

    // timer
    const [status, setStatus] = useState('TRABAJO');
    const [timeRemaining, setTimeRemaining] = useState(INITIAL_TIME);
    const [isActive, setIsActive] = useState(false);

    // modal
    const [showModal1, setShowModal1] = useState(false);
    const [showModal2, setShowModal2] = useState(false);
    const [fatigueLevel, setFatigueLevel] = useState(3);
    const [timeShortage, setTimeShortage] = useState(null);

    // --------------------------------- FUNCTIONS ---------------------------------

    const formatTime = (timeInSeconds) => {
        const minutes = Math.floor(timeInSeconds / 60);
        const seconds = timeInSeconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    };

    const startNextPomodoro = useCallback(() => {

        // try out function. could use for skip block ? depende de las entradas

        const nextStatus = status === 'TRABAJO' ? 'DESCANSO' : 'TRABAJO';
        const nextTime = nextStatus === 'TRABAJO' ? WORK_TIME : BREAK_TIME;

        setStatus(nextStatus);
        setTimeRemaining(nextTime);
        setIsActive(true);
        console.log(`[ACTION] Next phase: ${nextStatus} for ${nextTime / 60} minutes.`);
    }, [status]);

    const handlePauseToggle = () => {
        setIsActive(prev => {
            console.log(`[ACTION] Pause button clicked. Timer set to ${!prev ? 'Active (Running)' : 'Inactive (Paused)'}`);
            return !prev;
        });
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

    // --------------------------------- MODAL HANDLERS ---------------------------------
    // simulating submissions lol
    const handleFatigueSubmit = (level) => {
        console.log(`[SUBMIT] Fatigue: Level ${level}.`);
        setShowModal1(false);
        setShowModal2(true);
    };

    const handleTimeShortageSubmit = (answer) => {
        setTimeShortage(answer);
        console.log(`[SUBMIT] Tired: ${answer}.`);
        setShowModal2(false);
        startNextPomodoro();
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
            setShowModal1(true);
            console.log(`[TIMER] ${status} time over. Open modal.`);
        }

        return () => clearInterval(interval);
    }, [isActive, timeRemaining, status]);

    // --------------------------------- DYNAMIC STATES  ---------------------------------
    const timerText = useMemo(() => formatTime(timeRemaining), [timeRemaining]);
    const isTimeOver = timeRemaining === 0;

    // changes style classes based on status
    const pauseButtonClass = isActive ? 'pause-button-active' : 'pause-button-inactive';

    // calculates slider fill percentage for css animation
    const sliderFillPercent = ((fatigueLevel - 1) / 4) * 100;

    return (
        <div className="app-container">
            <Header />
            <main className="main-content">
                {/* STATUS TEXT */}
                <p className={`status-text`}>
                    {status}
                </p>

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
                        >
                            {isActive ? <Pause size={40} /> : <Play size={40} />}
                        </button>
                    </div>
                </div>

                {/* END AND SKIP BUTTONS*/}
                <div className="control-buttons-group">
                    <button
                        onClick={handleEndBlock}
                        className="control-button"
                        disabled={isTimeOver}
                    >
                        <Clock size={20} /> Terminar bloque
                    </button>

                    <button
                        onClick={handleSkipBlock}
                        className="control-button"
                    >
                        <Zap size={20} /> Saltar bloque
                    </button>
                </div>

                {/* RESTART BUTTON */}
                <div className="restart-group">
                    <button
                        onClick={startNextPomodoro}
                        className="restart-button"
                    >
                        <Clock size={40} />
                    </button>
                    Generar siguiente
                    <br />
                    pomodoro
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