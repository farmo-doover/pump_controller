import RemoteAccess from 'doover_home/RemoteAccess';
import {
    Button, Dialog, DialogActions, DialogContent, DialogTitle, TextField,
    FormControl, FormLabel, RadioGroup, FormControlLabel, Radio, Box,
    InputAdornment, Grid, Typography, ToggleButtonGroup, ToggleButton,
    Slider
} from '@mui/material';
import React, { Component } from 'react';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFnsV3';
import { addDays, addWeeks, eachDayOfInterval, eachWeekOfInterval, format } from 'date-fns';

import RemoveCircleIcon from '@mui/icons-material/RemoveCircle';
import EditIcon from '@mui/icons-material/Edit';
import { color } from '@mui/system';
// code is as follows:
const PAGE_SLOT_MAX = 10;

class TimeSlot {
    constructor(startTime, duration, edited = 0, mode = { type: '' }, color = '#FFFFFF') {
        this.startTime = startTime;
        this.duration = duration;
        this.edited = edited;
        this.mode = mode;
        this.color = color;
    }
}

class Schedule {
    constructor(name, frequency, startTime, endTime, duration, mode = { type: '' }, color = '#FFFFFF', edited = 0) {
        this.name = name;
        this.frequency = frequency;
        this.startTime = startTime;
        this.endTime = endTime;
        this.duration = duration;
        this.mode = mode;
        this.timeSlots = [];
        this.color = color;
        this.edited = edited;
    }

    addTimeSlot(timeSlot) {
        this.timeSlots.push(timeSlot);
    }

    removeTimeSlot(index) {
        this.timeSlots.splice(index, 1);
    }

    isEmpty() {
        return this.timeSlots.length === 0;
    }
}

export default class RemoteComponent extends RemoteAccess {
    constructor(props) {
        super(props);
        this.state = {
            open: false,
            editOpen: false,
            deleteOpen: false,
            clearAllOpen: false,
            editIndex: -1,
            deleteIndex: -1,
            editSchedule: null,
            editScheduleName: '',
            startDate: new Date(),
            endDate: new Date(),
            duration: 1,
            frequency: 'once',
            scheduleName: '',
            schedules: [],
            modes: [],
            selectedMode: '',
            modeParams: {},
            mainParams: {
                scheduleNameSingle: 'Schedule',
                scheduleNamePlural: 'Schedules',
                timeslotNameSingle: 'Timeslot',
                timeslotNamePlural: 'Timeslots'
            },
            scheduleColors: [],
            editingSchedule: false,
            currentPage: 0,
            isPageInputActive: false,
            pageInputValue: '',
            sortedTimeSlots: [],
            sortedSchedules: [],
            toggleView: 'Timeslots',
            inSchedules: [],
            editingSchedule: false,
            editFrequency: 'once',
            startDateError: "",
            endDateError: "",
            editError: "",
            hasModes: false,
        };
        this.updateUiStates = this.updateUiStates.bind(this);
    }

    handleClickOpen = () => {
        const now = new Date();
        const roundedMinutes = Math.ceil(now.getMinutes() / 15) * 15;
        const roundedDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours(), roundedMinutes);

        this.setState({ 
            open: true, 
            scheduleName: '',
            startDate: roundedDate,
            endDate: new Date(roundedDate.getTime() + 60 * 60 * 1000),
            duration: 1,
            frequency: 'once',
            mode: { type: '' }  // Reset mode to an object with an empty type
        });
    };

    handleClose = () => {
        this.setState({ open: false, startDateError: "", endDateError: ""  });
    };

    extractModeParams = (mode) => {
        const params = {};
        for (const key in mode) {
            if (key !== 'type') {
                params[key] = mode[key];
            }
        }
        return params;
    };

    handleEditOpen = (index) => {
        const { toggleView, sortedTimeSlots, sortedSchedules } = this.state;
    
        if (toggleView === 'Timeslots') {
            const slot = sortedTimeSlots[index];
            if (slot) {
                const scheduleObj = this.state.schedules.find(s => s.name === slot.scheduleName);
                this.setState({
                    editOpen: true,
                    editIndex: index,
                    startDate: new Date(slot.startTime),
                    endDate: new Date(slot.startTime.getTime() + slot.duration * 3600 * 1000),
                    duration: slot.duration,
                    editSchedule: slot.scheduleName,
                    editScheduleName: slot.scheduleName,
                    editFrequency: scheduleObj ? scheduleObj.frequency : 'once',
                    selectedMode: slot.mode ? slot.mode.type : '',
                    modeParams: this.extractModeParams(slot.mode || {}),
                    editingSchedule: false
                });
            }
        } else {  // 'Schedules' view
            const schedule = sortedSchedules[index];
            if (schedule) {
                this.setState({
                    editOpen: true,
                    editIndex: index,
                    startDate: new Date(schedule.startTime),
                    endDate: new Date(schedule.endTime),
                    duration: schedule.duration,
                    editSchedule: schedule.name,
                    editScheduleName: schedule.name,
                    editFrequency: schedule.frequency,
                    selectedMode: schedule.mode ? schedule.mode.type : '',
                    modeParams: this.extractModeParams(schedule.mode || {}),
                    editingSchedule: true
                });
            }
        }
    };

    handleEditFrequencyChange = (event) => {
        this.setState({ editFrequency: event.target.value });
    };

    handleEditClose = () => {
        this.setState({ editOpen: false, editError: "" });
    };

    handleDeleteOpen = (index) => {
        this.setState({ deleteOpen: true, deleteIndex: index });
    };

    handleDeleteClose = () => {
        this.setState({ deleteOpen: false });
    };

    handleClearAllOpen = () => {
        this.setState({ clearAllOpen: true });
    };

    handleClearAllClose = () => {
        this.setState({ clearAllOpen: false });
    };

    handleDateChange = (date) => {
        this.setState({ startDate: date });
    };

    handleEndDateChange = (date) => {
        this.setState({ endDate: date });
    };

    handleDurationChange = (event) => {
        this.setState({ duration: event.target.value });
    };

    handleFrequencyChange = (event) => {
        this.setState({ frequency: event.target.value });
    };

    handleScheduleNameChange = (event) => {
        this.setState({ scheduleName: event.target.value });
    };

    handleEditScheduleNameChange = (event) => {
        this.setState({ editScheduleName: event.target.value });
    };

    handleModeChange = (event) => {
        const selectedMode = event.target.value;
        this.setState({ 
            selectedMode,
            modeParams: {} // Reset params when mode changes
        });
    };

    handleViewChange = () => {
        this.setState(prevState => ({ 
            toggleView: prevState.toggleView === 'Timeslots' ? 'Schedules' : 'Timeslots',
            currentPage: 0  // Reset to first page when switching views
        }), this.sortSchedules);  // Re-sort after changing view
    };

    handleParamChange = (paramName, value) => {
        this.setState(prevState => ({
            modeParams: {
                ...prevState.modeParams,
                [paramName]: value
            }
        }));
    };

    generateColors(count) {
        const colors = [];
        const saturation = 60;  // Value from 0 to 255
        const lightness = 220;  // Value from 0 to 255, middle value for 50% lightness
        
        for (let i = 0; i < count; i++) {
            const hue = Math.round((i / count) * 360);  // Distribute hues evenly
            const hslColor = `hsl(${hue}, ${saturation}, ${lightness})`;
            const hexColor = this.hslToHex(hue, saturation / 255, lightness / 255);
            colors.push(hexColor);
        }
        
        return colors;
    }
    
    // Helper function to convert HSL to Hex
    hslToHex(h, s, l) {
        h /= 360;
        let r, g, b;
        if (s === 0) {
            r = g = b = l; // achromatic
        } else {
            const hue2rgb = (p, q, t) => {
                if (t < 0) t += 1;
                if (t > 1) t -= 1;
                if (t < 1/6) return p + (q - p) * 6 * t;
                if (t < 1/2) return q;
                if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
                return p;
            };
            const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
            const p = 2 * l - q;
            r = hue2rgb(p, q, h + 1/3);
            g = hue2rgb(p, q, h);
            b = hue2rgb(p, q, h - 1/3);
        }
        const toHex = x => {
            const hex = Math.round(x * 255).toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        };
        return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
    }

    formatModeObject = () => {
        const { selectedMode, modeParams } = this.state;
        const modeObject = { type: selectedMode };
        
        const selectedModeObj = this.state.modes.find(mode => mode.name === selectedMode);
        if (selectedModeObj && selectedModeObj.params) {
            selectedModeObj.params.forEach(param => {
                if (modeParams.hasOwnProperty(param.name)) {
                    modeObject[param.name] = modeParams[param.name];
                }
            });
        }

        return modeObject;
    }

    pushChanges = () => {
        const apiWrapper = window.dooverDataAPIWrapper;
        const agent_id = this.getUi().agent_key;
    
        apiWrapper.get_temp_token().then((token) => {
            apiWrapper.get_channel_aggregate(
                {
                    agent_id: agent_id,
                    channel_name: 'schedules',
                },
                token.token
            ).then((currentData) => {
                const scheduleColors = this.generateColors(this.state.schedules.length);
                const updatedSchedules = this.state.schedules.length > 0 ? this.state.schedules.map((schedule, index) => {
                    
                    schedule.color = scheduleColors[index];
                    schedule.timeSlots.forEach(slot => {
                        slot.color = slot.edited === 1 ? '#FFFFFF' : scheduleColors[index];
                    });
    
                    return {
                        schedule_name: schedule.name,
                        frequency: schedule.frequency,
                        start_time: new Date(schedule.startTime).getTime() / 1000,
                        end_time: new Date(schedule.endTime).getTime() / 1000,
                        duration: schedule.duration,
                        mode: schedule.mode,
                        edited: schedule.edited,
                        timeslots: schedule.timeSlots.map(slot => {
                            //console.log("slot",slot);
                            return {
                                start_time: new Date(slot.startTime).getTime() / 1000,
                                end_time: new Date(slot.startTime).getTime() / 1000 + slot.duration * 3600,
                                duration: slot.duration,
                                mode: slot.mode,
                                edited: slot.edited,
                            };
                        })
                    };
                }) : [];
    
                const payload = {
                    modes: currentData.aggregate.payload.modes || [],
                    schedules: updatedSchedules
                };
    
                apiWrapper.post_channel_aggregate(
                    {
                        agent_id: agent_id,
                        channel_name: 'schedules',
                    },
                    JSON.stringify(payload),
                    token.token
                );
    
                // Update the state with new colors
                this.setState({
                    schedules: this.state.schedules.map((schedule, index) => ({
                        ...schedule,
                        color: scheduleColors[index],
                        timeSlots: schedule.timeSlots.map(slot => ({
                            ...slot,
                            color: slot.edited === 1 ? '#FFFFFF' : scheduleColors[index]
                        }))
                    }))
                });
                
            }).catch((error) => {
                console.error('Error fetching current channel data:', error);
            });
        }).catch((error) => {
            console.error('Error getting temp token:', error);
        });
    };       

    createTimeslot = (startTime, duration, edited = 0) => {
        return new TimeSlot(new Date(startTime), duration, edited);
    };

    handleSave = () => {
        const { startDate, endDate, duration, frequency, scheduleName, mode, schedules } = this.state;
        const now = new Date();
        const twentyFourHoursAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    
        if (startDate < twentyFourHoursAgo) {
            this.setState({ startDateError: "Start date cannot be more than 24 hours in the past." });
            return;
        }
    
        if (frequency !== 'once' && endDate <= startDate) {
            this.setState({ endDateError: "End date must be after the start date for recurring schedules." });
            return;
        }
    
        this.setState({ startDateError: "", endDateError: "" });
    
        if (frequency === 'once') {
            const checkStart = startDate.getTime();
            const checkEnd = checkStart + duration * 3600 * 1000;
            let valStart;
            let valEnd;
            let collide = false;
            for (const [indexSched,valSched] of this.state.schedules.entries()) {
                for (const [indexSlot,valSlot] of valSched.timeSlots.entries()) {
                    valStart = valSlot.startTime.getTime();
                    valEnd = valStart + valSlot.duration * 3600 * 1000;
                    if ((checkStart <= valStart && checkEnd >= valStart)
                        || (checkStart < valEnd && checkEnd >= valEnd)
                    ) {                 
                        this.setState(prevState => {
                            const updatedSchedules = [...prevState.schedules];
                            const updatedTimeSlots = [...updatedSchedules[indexSched].timeSlots];
        
                            updatedTimeSlots[indexSlot] = {
                                ...updatedTimeSlots[indexSlot],
                                startTime: new Date(Math.min(checkStart,valStart)),
                                endTime: new Date(Math.max(checkEnd,valEnd)),
                                duration: (Math.max(checkEnd,valEnd) - Math.min(checkStart,valStart)) / 3600 / 1000,
                                edited: 1,
                            };
        
                            updatedSchedules[indexSched] = {
                                ...updatedSchedules[indexSched],
                                timeSlots: updatedTimeSlots,
                            };
        
                            return {
                                ...prevState,
                                schedules: updatedSchedules,
                            };
                        });
                        this.pushChanges();
                        collide = true;
                        break; 
                    }
                } 
            }
            if (collide === false) {
                const modeObject = this.formatModeObject();
                const newSchedule = new Schedule('Once', frequency, startDate, endDate, duration, modeObject);
                newSchedule.addTimeSlot(new TimeSlot(startDate, duration, 0, modeObject));
                const scheduleColor = this.generateColors(schedules.length + 1).pop();
                newSchedule.color = scheduleColor;
                newSchedule.timeSlots.forEach(slot => {
                    slot.color = scheduleColor;
                });
            
                this.setState((prevState) => ({
                    schedules: [...prevState.schedules, newSchedule],
                    open: false,
                    selectedMode: '',
                    modeParams: {}
                }), () => {
                    this.sortSchedules();
                    this.pushChanges();
                });
            
                } else {
                    this.setState({
                        open: false,
                        selectedMode: '',
                        modeParams: {}
                    }, () => {
                        this.sortSchedules();
                        this.pushChanges();
                    });
            
                }

        } else {
            let currentDate = new Date(startDate);
            let schedCreated = false;
            let newSchedule;
            let modeObject;
            let collideAsSuch = 0;
            
            while (currentDate <= endDate) {
                let valStart;
                let valEnd;
                let collide = false;
                let checkStart = currentDate.getTime();
                let checkEnd = checkStart + duration * 3600 * 1000;
                middleLoop:
                for (const [indexSched,valSched] of this.state.schedules.entries()) {
                    for (const [indexSlot,valSlot] of valSched.timeSlots.entries()) {
                        valStart = valSlot.startTime.getTime();
                        valEnd = valStart + valSlot.duration * 3600 * 1000;
                        if ((checkStart <= valStart && checkEnd >= valStart)
                            || (checkStart < valEnd && checkEnd >= valEnd)
                        ) {                 
                            this.setState(prevState => {
                                const updatedSchedules = [...prevState.schedules];
                                const updatedTimeSlots = [...updatedSchedules[indexSched].timeSlots];
            
                                updatedTimeSlots[indexSlot] = {
                                    ...updatedTimeSlots[indexSlot],
                                    startTime: new Date(Math.min(checkStart,valStart)),
                                    endTime: new Date(Math.max(checkEnd,valEnd)),
                                    duration: (Math.max(checkEnd,valEnd) - Math.min(checkStart,valStart)) / 3600 / 1000,
                                };
            
                                updatedSchedules[indexSched] = {
                                    ...updatedSchedules[indexSched],
                                    timeSlots: updatedTimeSlots,
                                    edited: 1, 
                                };
            
                                return {
                                    ...prevState,
                                    schedules: updatedSchedules,
                                };
                            });
                            this.pushChanges();
                            collide = true;
                            collideAsSuch = 1;
                            break middleLoop; 
                        } 
                    }
                }
                if (collide === false) {
                    if (!schedCreated) {
                        modeObject = this.formatModeObject();
                        newSchedule = new Schedule(scheduleName, frequency, startDate, endDate, duration, modeObject);
                        schedCreated = true;
                    }
                    newSchedule.addTimeSlot(new TimeSlot(new Date(currentDate), duration, 0, modeObject));
                    newSchedule.edited = collideAsSuch;
                    schedCreated = true;
                }
                if (frequency === 'daily') {
                    currentDate = addDays(currentDate, 1);
                } else if (frequency === 'weekly') {
                    currentDate = addWeeks(currentDate, 1);
                }
            }
            if (schedCreated) {
                const scheduleColor = this.generateColors(schedules.length + 1).pop();
                newSchedule.color = scheduleColor;
                newSchedule.timeSlots.forEach(slot => {
                    slot.color = scheduleColor;
                });
                this.setState((prevState) => ({
                    schedules: [...prevState.schedules, newSchedule],
                    open: false,
                    selectedMode: '',
                    modeParams: {}
                }), () => {
                    this.sortSchedules();
                    this.pushChanges();
                });
            } else {
                this.setState({
                    open: false,
                    selectedMode: '',
                    modeParams: {}
                }, () => {
                    this.sortSchedules();
                    this.pushChanges();
                });
            }
        }
    };


    updateTimeslots = (schedule, newStartTime, newEndTime, newDuration, newFrequency, modeObject) => {
        let updatedTimeslots = [];
    
        if (newFrequency === 'once') {
            updatedTimeslots = [new TimeSlot(newStartTime, newDuration, 0, modeObject, schedule.color)];
        } else {
            let currentTime = new Date(newStartTime);
            while (currentTime <= newEndTime) {
                const existingSlot = schedule.timeSlots.find(slot => 
                    slot.startTime.getTime() === currentTime.getTime()
                );
    
                if (existingSlot && existingSlot.edited === 1) {
                    updatedTimeslots.push(new TimeSlot(existingSlot.startTime, existingSlot.duration, 1, existingSlot.mode, '#FFFFFF'));
                } else {
                    updatedTimeslots.push(new TimeSlot(new Date(currentTime), newDuration, 0, modeObject, schedule.color));
                }
    
                if (newFrequency === 'daily') {
                    currentTime = addDays(currentTime, 1);
                } else if (newFrequency === 'weekly') {
                    currentTime = addWeeks(currentTime, 1);
                }
            }
        }
    
        // Preserve edited timeslots that fall outside the new schedule range
        schedule.timeSlots.forEach(slot => {
            if (slot.edited === 1 && (slot.startTime < newStartTime || slot.startTime > newEndTime)) {
                updatedTimeslots.push(new TimeSlot(slot.startTime, slot.duration, 1, slot.mode, '#FFFFFF'));
            }
        });
    
        updatedTimeslots.sort((a, b) => a.startTime - b.startTime);
    
        return updatedTimeslots;
    };


    handleEditSave = () => {
        // if (frequency !== 'once' && endDate <= startDate) {
        //     this.setState({ editError: "editing in this way would cause a conflict. Please try again" });
        //     return;
        // }
    
        // this.setState({ editError: ""});

        const { startDate, endDate, duration, editIndex, sortedTimeSlots, sortedSchedules, toggleView, editFrequency, selectedMode, modeParams, editScheduleName } = this.state;
        const modeObject = this.formatModeObject();

        if (toggleView === 'Timeslots') {

            const checkStart = startDate.getTime();
            const checkEnd = checkStart + duration * 3600 * 1000;
            let valStart;
            let valEnd;
            for (const valSched of this.state.schedules) {
                for (const valSlot of valSched.timeSlots) {
                    valStart = valSlot.startTime.getTime();
                    valEnd = valStart + valSlot.duration * 3600 * 1000;
                    if ((checkStart <= valStart && checkEnd >= valStart)
                        || (checkStart < valEnd && checkEnd >= valEnd)
                    ) {
                        this.setState({ editError: "editing in this way would cause a conflict. Please try again" });
                        return; 
                    }
                }
            }

            this.setState({ editError: ""})

            const timeSlot = sortedTimeSlots[editIndex];
            if (timeSlot) {
                this.setState(prevState => {
                    const updatedSchedules = prevState.schedules.map(schedule => {
                        if (schedule.name === timeSlot.scheduleName) {
                            const updatedTimeSlots = schedule.timeSlots.map(slot => 
                                slot.startTime.getTime() === timeSlot.startTime.getTime()
                                    ? new TimeSlot(new Date(startDate), duration, 1, modeObject)
                                    : slot
                            );
                            return { ...schedule, timeSlots: updatedTimeSlots, edited: 1 };
                        }
                        return schedule;
                    });
                    return { schedules: updatedSchedules, editOpen: false, selectedMode: '', modeParams: {} };
                }, () => {
                    this.sortSchedules();
                    this.pushChanges();
                });
            }
        } else {

            let currentDate = new Date(startDate);
            let modeObject;
            
            while (currentDate <= endDate) {
                let valStart;
                let valEnd;
                let checkStart = currentDate.getTime();
                let checkEnd = checkStart + duration * 3600 * 1000;
                for (const valSched of this.state.schedules) {
                    if (valSched.name === editScheduleName) {
                        continue;
                    }
                    for (const valSlot of valSched.timeSlots) {
                        valStart = valSlot.startTime.getTime();
                        valEnd = valStart + valSlot.duration * 3600 * 1000;
                        if ((checkStart <= valStart && checkEnd >= valStart)
                            || (checkStart < valEnd && checkEnd >= valEnd)
                        ) {
                            this.setState({ editError: "editing in this way would cause a conflict. Please try again" });
                            return;
                        }
                    }
                }
                if (editFrequency === 'daily') {
                    currentDate = addDays(currentDate, 1);
                } else if (editFrequency === 'weekly') {
                    currentDate = addWeeks(currentDate, 1);
                }
            }

            this.setState({ editError: ""})

            const scheduleToEdit = sortedSchedules[editIndex];
            if (scheduleToEdit) {
                this.setState(prevState => {
                    const updatedSchedules = prevState.schedules.map(schedule => {
                        if (schedule.name === scheduleToEdit.name) {
                            let updatedTimeslots = this.updateTimeslots(
                                schedule,
                                startDate,
                                endDate,
                                duration,
                                editFrequency,
                                modeObject
                            );
    
                            return {
                                ...schedule,
                                name: editScheduleName,
                                frequency: editFrequency,
                                startTime: startDate,
                                endTime: endDate,
                                duration: duration,
                                mode: modeObject,
                                timeSlots: updatedTimeslots
                            };
                        }
                        return schedule;
                    });
    
                    return { 
                        schedules: updatedSchedules, 
                        editOpen: false,
                        selectedMode: '',
                        modeParams: {},
                        editScheduleName: ''
                    };
                }, () => {
                    this.sortSchedules();
                    this.pushChanges();
                });
            }
        }
    };


    handleDelete = () => {
        const { deleteIndex, sortedTimeSlots, sortedSchedules, toggleView } = this.state;
    
        if (toggleView === 'Timeslots') {
            const { scheduleName, startTime } = sortedTimeSlots[deleteIndex];
    
            this.setState(prevState => {
                const updatedSchedules = prevState.schedules.map(schedule => {
                    if (schedule.name === scheduleName) {
                        const updatedTimeSlots = schedule.timeSlots.filter(
                            slot => slot.startTime.getTime() !== startTime.getTime()
                        );
                        return {
                            ...schedule,
                            timeSlots: updatedTimeSlots
                        };
                    }
                    return schedule;
                });
    
                // Remove any schedules that now have no timeslots
                const filteredSchedules = updatedSchedules.filter(schedule => schedule.timeSlots.length > 0);
    
                return {
                    schedules: filteredSchedules,
                    deleteOpen: false
                };
            }, () => {
                this.sortSchedules();
                this.pushChanges();
            });
        } else if (toggleView === 'Schedules') {
            const scheduleToDelete = sortedSchedules[deleteIndex];
            this.setState(prevState => ({
                schedules: prevState.schedules.filter(schedule => schedule.name !== scheduleToDelete.name),
                deleteOpen: false
            }), () => {
                this.sortSchedules();
                this.pushChanges();
            });
        }
    };

    handleClearAll = () => {
        this.setState({
            schedules: [],
            currentPage: 0,
            sortedTimeSlots: [],
            sortedSchedules: [],
            clearAllOpen: false
        }, () => {
            this.pushChanges();
        });
    };

    formatDateTime = (date) => {
        return format(date, 'dd/M/yy h:mma');
    };

    getcurrentPageSlots = () => {
        const { sortedTimeSlots, currentPage } = this.state;
        const startIndex = currentPage * PAGE_SLOT_MAX;
        const endIndex = startIndex + PAGE_SLOT_MAX;
        return sortedTimeSlots.slice(startIndex, endIndex);
    };

    getCurrentPageSchedule = () => {
        const { sortedSchedules, currentPage } = this.state;
        const startIndex = currentPage * PAGE_SLOT_MAX;
        let endIndex
        if (sortedSchedules.length < (currentPage + 1) * PAGE_SLOT_MAX) {
            endIndex = sortedSchedules.length;
        } else {
            endIndex = (currentPage + 1) * PAGE_SLOT_MAX;
        }
        return sortedSchedules.slice(startIndex, endIndex);
    }

    handleNextPage = () => {
        this.setState((prevState) => ({
            currentPage: prevState.currentPage + 1,
            isPageInputActive: false,
            pageInputValue: ''
        }));
    };

    handlePreviousPage = () => {
        if (!this.state.isPageInputActive) {
            this.setState((prevState) => ({
                currentPage: prevState.currentPage - 1
            }));
        } else {
            this.setState({
                isPageInputActive: false,
                pageInputValue: ''
            });
        }
    };

    handlePageInputToggle = () => {
        this.setState((prevState) => ({
            isPageInputActive: !prevState.isPageInputActive,
            pageInputValue: ''
        }));
    };

    handlePageInputChange = (event) => {
        this.setState({ pageInputValue: event.target.value });
    };

    handleJumpToPage = () => {
        const { pageInputValue, sortedTimeSlots } = this.state;
        const totalPages = Math.ceil(sortedTimeSlots.length / PAGE_SLOT_MAX);
        const pageNumber = parseInt(pageInputValue, 10);

        if (pageNumber >= 1 && pageNumber <= totalPages) {
            this.setState({
                currentPage: pageNumber - 1,
                isPageInputActive: false,
                pageInputValue: ''
            });
        } else {
            this.setState({
                isPageInputActive: false,
                pageInputValue: ''
            });
        }
    };

    async updateUiStates() {
        try {
            let agent_id = this.getUi().agent_key;
            const token = await window.dooverDataAPIWrapper.get_temp_token();
            const schedules = await window.dooverDataAPIWrapper.get_channel_aggregate(
                {
                    agent_id: agent_id,
                    channel_name: "schedules",
                },
                token.token
            );
            return schedules.aggregate.payload;
        } catch (err) {
            console.error('ERROR:', err);
            this.setState({ loading: false });
            return null;
        }
    }

    sortSchedules = () => {
        if (!this.state.schedules || this.state.schedules.length === 0) {
            this.setState({ 
                sortedTimeSlots: [],
                sortedSchedules: []
            });
            return;
        }

        const validSchedules = this.state.schedules.filter(schedule => 
            schedule && typeof schedule === 'object' && Array.isArray(schedule.timeSlots)
        );
        const allTimeSlots = validSchedules.flatMap(schedule =>
            schedule.timeSlots.map(slot => ({
                ...slot,
                scheduleName: schedule.name || 'Unnamed Schedule',
                color: slot.edited === 1 ? '#FFFFFF' : schedule.color
            }))
        );
        allTimeSlots.sort((a, b) => new Date(a.startTime) - new Date(b.startTime));

        const allSchedules = validSchedules.map(schedule => ({
            scheduleName: schedule.name || 'Unnamed Schedule',
            frequency: schedule.frequency || 'once',
            startTime: new Date(schedule.startTime || Date.now()),
            endTime: new Date(schedule.endTime || Date.now()),
            duration: schedule.duration || 0,
            color: schedule.color
        }));
        allSchedules.sort((a, b) => a.startTime - b.startTime);
        this.setState({ 
            sortedTimeSlots: allTimeSlots,
            sortedSchedules: validSchedules
        });
    };

    componentDidMount() {
        this.updateUiStates()
            .then((payload) => {
                const scheduleColors = this.generateColors(payload.schedules.length);
                const schedules = Array.isArray(payload.schedules) ? payload.schedules.map((scheduleData, index) => {
                    // Ensure scheduleData is an object and has necessary properties
                    if (typeof scheduleData !== 'object' || !scheduleData) {
                        console.warn("Invalid schedule data:", scheduleData);
                        return null;
                    }
                    const { start_time, end_time, frequency, schedule_name, timeslots, duration, mode } = scheduleData;
                    
                    const schedule = new Schedule(
                        schedule_name,
                        frequency,
                        new Date(start_time * 1000),
                        new Date(end_time * 1000), 
                        duration,
                        mode || { type: '' },
                        scheduleColors[index]
                    );

                    if (Array.isArray(timeslots)) {
                        timeslots.forEach((timeslot) => {
                            if (typeof timeslot === 'object' && timeslot && (timeslot.end_time > (Date.now() / 1000))) {
                                const { start_time: tsStartTime, end_time: tsEndTime, edited, mode: tsMode } = timeslot;
                                const slotDuration = (tsEndTime - tsStartTime) / 3600;
                                let slotColor = scheduleColors[index];
                                if (edited === 1) {
                                    slotColor = '#FFFFFF';
                                }
                                schedule.addTimeSlot(new TimeSlot(
                                    new Date(tsStartTime * 1000), 
                                    slotDuration,
                                    edited || 0,
                                    tsMode || { type: '' },
                                    slotColor
                                ));
                            }
                        });
                    } else {
                        console.warn("Invalid timeslots data for schedule:", schedule_name);
                    }

                    return schedule;
                }).filter(Boolean) : [];

                const mainParams = payload.main_params || {};
                const updatedMainParams = {
                    scheduleNameSingle: mainParams.schedule_name_single || this.state.mainParams.scheduleNameSingle,
                    scheduleNamePlural: mainParams.schedule_name_plural || this.state.mainParams.scheduleNamePlural,
                    timeslotNameSingle: mainParams.timeslot_name_single || this.state.mainParams.timeslotNameSingle,
                    timeslotNamePlural: mainParams.timeslot_name_plural || this.state.mainParams.timeslotNamePlural
                };

                const modes = Array.isArray(payload.modes) ? payload.modes : [];

                this.setState({
                    schedules,
                    modes: modes,
                    hasModes: modes.length > 0,
                    mainParams: updatedMainParams,
                    scheduleColors: scheduleColors
                    
                }, () => {
                    this.sortSchedules();
                });
                this.pushChanges();
            })
            .catch((err) => {
                console.error('ERROR:', err);
            });
    }

    renderModeSelection = () => {
        const { modes, selectedMode, modeParams } = this.state;

        if (modes.length === 0) {
            return null;
        }

        const selectedModeObj = modes.find(mode => mode.name === selectedMode);

        return (
            <FormControl component="fieldset" fullWidth margin="normal">
                <FormLabel component="legend">Mode</FormLabel>
                <RadioGroup
                    name="mode"
                    value={selectedMode}
                    onChange={this.handleModeChange}
                >
                    {modes.map((mode) => (
                        <FormControlLabel
                            key={mode.name}
                            value={mode.name}
                            control={<Radio />}
                            label={mode.display_name}
                        />
                    ))}
                </RadioGroup>

                {selectedModeObj && selectedModeObj.params.length > 0 && (
                    <Box mt={2}>
                        {selectedModeObj.params.map(param => (
                            <Box key={param.name} mt={2}>
                                <Typography gutterBottom>
                                    {param.display_name}
                                </Typography>
                                <Slider
                                    value={modeParams[param.name] !== undefined ? modeParams[param.name] : param.min}
                                    onChange={(_, value) => this.handleParamChange(param.name, value)}
                                    min={param.min}
                                    max={param.max}
                                    step={0.01}
                                    valueLabelDisplay="on"
                                />
                            </Box>
                        ))}
                    </Box>
                )}
            </FormControl>
        );
    };


    render() {

        //console.log("state",this.state);

        const { currentPage, isPageInputActive, pageInputValue, frequency, sortedTimeSlots, sortedSchedules, deleteOpen, clearAllOpen, toggleView, mainParams, hasModes } = this.state;
        let currentPageSlots;
        let sortedRows;
        if (toggleView === 'Timeslots') {
            sortedRows = sortedTimeSlots
            currentPageSlots = this.getcurrentPageSlots();
        } else {
            sortedRows = sortedSchedules
            currentPageSlots = this.getCurrentPageSchedule();
        }

        const totalPages = Math.ceil(sortedRows.length / PAGE_SLOT_MAX);

        return (
            <Box>
                <Box display="flex" justifyContent="space-between" alignItems="center" position="relative" >
                    <Button variant="contained" color="primary" onClick={this.handleClickOpen} sx={{ height: "50px", margin: "0px" }}>
                        Create {mainParams.scheduleNameSingle}
                    </Button>
                    <ToggleButtonGroup
                        value={toggleView}
                        exclusive
                        onChange={this.handleViewChange}
                        sx={{ height: "50px" }}
                    >
                        <ToggleButton value="Schedules" sx={{ textTransform: 'none' }}>{mainParams.scheduleNamePlural}</ToggleButton>
                        <ToggleButton value="Timeslots" sx={{ textTransform: 'none' }}>{mainParams.timeslotNamePlural}</ToggleButton>
                    </ToggleButtonGroup>
                    {sortedRows.length > 0 && (
                        <Button
                            variant="contained"
                            color="secondary"
                            onClick={this.handleClearAllOpen}
                            sx={{
                                height: "50px",
                                right: 0,
                                backgroundColor: '#F44336',
                                color: '#FFFFFF',
                                '&:hover': {
                                    backgroundColor: '#D32F2F'
                                }
                            }}
                        >
                            CLEAR ALL
                        </Button>
                    )}
                </Box>
                <Dialog open={this.state.open} onClose={this.handleClose}>
                    <DialogTitle>Create {mainParams.scheduleNameSingle}</DialogTitle>
                    <DialogContent>
                        <FormControl fullWidth margin="normal">
                            <FormLabel component="legend" sx={{ color: '#000000' }}>Start Date/Time</FormLabel>
                            <LocalizationProvider dateAdapter={AdapterDateFns}>
                                <DateTimePicker
                                    value={this.state.startDate}
                                    onChange={this.handleDateChange}
                                    renderInput={(params) => <TextField {...params} fullWidth margin="normal" />}
                                />
                            </LocalizationProvider>
                            {this.state.startDateError && (
                                <Typography color="error">{this.state.startDateError}</Typography>
                            )}
                        </FormControl>
                        <FormControl component="fieldset" fullWidth margin="normal">
                            <FormLabel component="legend" sx={{ color: '#000000' }}>Duration</FormLabel>
                            <Box display="flex" alignItems="center">
                                <TextField
                                    type="number"
                                    value={this.state.duration}
                                    onChange={this.handleDurationChange}
                                    InputProps={{
                                        endAdornment: <InputAdornment position="end">hrs</InputAdornment>,
                                    }}
                                    sx={{ width: '100px', marginRight: '10px' }}
                                />
                            </Box>
                        </FormControl>
                        <Box display="flex" alignItems="center">
                            <FormControl component="fieldset" margin="normal" sx={{ flex: '1 1 auto' }}>
                                <FormLabel component="legend" sx={{ color: '#000000', '&.Mui-focused': { color: '#000000' } }}>Frequency</FormLabel>
                                <RadioGroup
                                    name="frequency"
                                    value={this.state.frequency}
                                    onChange={this.handleFrequencyChange}
                                >
                                    <FormControlLabel value="once" control={<Radio />} label="Once" />
                                    <FormControlLabel value="daily" control={<Radio />} label="Daily" />
                                    <FormControlLabel value="weekly" control={<Radio />} label="Weekly" />
                                </RadioGroup>
                            </FormControl>
                            {frequency !== 'once' && (
                                <FormControl fullWidth margin="normal">
                                    <FormLabel component="legend" sx={{ color: '#000000' }}>Repeat until:</FormLabel>
                                    <LocalizationProvider dateAdapter={AdapterDateFns}>
                                        <DateTimePicker
                                            value={this.state.endDate}
                                            onChange={this.handleEndDateChange}
                                            renderInput={(params) => <TextField {...params} fullWidth margin="normal" />}
                                        />
                                    </LocalizationProvider>
                                    {this.state.endDateError && (
                                        <Typography color="error">{this.state.endDateError}</Typography>
                                    )}
                                </FormControl>
                            )}
                        </Box>
                        {frequency !== 'once' && (
                            <FormControl fullWidth margin="normal">
                                <FormLabel component="legend" sx={{ color: '#000000' }}>Schedule Name</FormLabel>
                                <TextField
                                    value={this.state.scheduleName}
                                    onChange={this.handleScheduleNameChange}
                                    fullWidth
                                />
                            </FormControl>
                        )}
                        {this.renderModeSelection()}
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={this.handleClose} color="primary">
                            Cancel
                        </Button>
                        <Button onClick={this.handleSave} color="primary">
                            Save
                        </Button>
                    </DialogActions>
                </Dialog>
                <Dialog open={this.state.editOpen} onClose={this.handleEditClose}>
                    <DialogTitle>
                        {this.state.editingSchedule 
                            ? `Edit ${mainParams.scheduleNameSingle}` 
                            : `Edit ${mainParams.timeslotNameSingle}`}
                    </DialogTitle>
                    <DialogContent>
                    {this.state.editingSchedule && (
                            <FormControl fullWidth margin="normal">
                                <FormLabel component="legend">Schedule Name</FormLabel>
                                <TextField
                                    value={this.state.editScheduleName}
                                    onChange={this.handleEditScheduleNameChange}
                                    fullWidth
                                />
                            </FormControl>
                        )}
                        <FormControl fullWidth margin="normal">
                            <FormLabel component="legend">Start Date/Time</FormLabel>
                            <LocalizationProvider dateAdapter={AdapterDateFns}>
                                <DateTimePicker
                                    value={this.state.startDate}
                                    onChange={(date) => this.setState({ startDate: date })}
                                    renderInput={(params) => <TextField {...params} fullWidth margin="normal" />}
                                />
                            </LocalizationProvider>
                        </FormControl>
                        {this.state.editingSchedule && (
                            <>
                                <FormControl component="fieldset" margin="normal">
                                    <FormLabel component="legend">Frequency</FormLabel>
                                    <RadioGroup
                                        name="editFrequency"
                                        value={this.state.editFrequency}
                                        onChange={(e) => this.setState({ editFrequency: e.target.value })}
                                    >
                                        <FormControlLabel value="once" control={<Radio />} label="Once" />
                                        <FormControlLabel value="daily" control={<Radio />} label="Daily" />
                                        <FormControlLabel value="weekly" control={<Radio />} label="Weekly" />
                                    </RadioGroup>
                                </FormControl>
                                {this.state.editFrequency !== 'once' && (
                                    <FormControl fullWidth margin="normal">
                                        <FormLabel component="legend">End Date/Time</FormLabel>
                                        <LocalizationProvider dateAdapter={AdapterDateFns}>
                                            <DateTimePicker
                                                value={this.state.endDate}
                                                onChange={(date) => this.setState({ endDate: date })}
                                                renderInput={(params) => <TextField {...params} fullWidth margin="normal" />}
                                            />
                                        </LocalizationProvider>
                                    </FormControl>
                                )}
                            </>
                        )}
                        <FormControl component="fieldset" fullWidth margin="normal">
                            <FormLabel component="legend">Duration</FormLabel>
                            <TextField
                                type="number"
                                value={this.state.duration}
                                onChange={(e) => this.setState({ duration: parseFloat(e.target.value) })}
                                InputProps={{
                                    endAdornment: <InputAdornment position="end">hrs</InputAdornment>,
                                }}
                            />
                        </FormControl>
                        {this.renderModeSelection()}
                    </DialogContent>
                    {this.state.editError && (
                                <Typography color="error">{this.state.editError}</Typography>
                            )}
                    <DialogActions>
                        <Button onClick={this.handleEditClose} color="primary">
                            Cancel
                        </Button>
                        <Button onClick={this.handleEditSave} color="primary">
                            Save
                        </Button>
                    </DialogActions>
                </Dialog>
                <Dialog
                    open={deleteOpen}
                    onClose={this.handleDeleteClose}
                >
                    <DialogTitle>Confirm Deletion</DialogTitle>
                    <DialogContent>
                        <Typography>
                            {toggleView === 'Timeslots'
                                ? `Are you sure you want to delete this ${mainParams.timeslotNameSingle}?`
                                : `Are you sure you want to delete this ${mainParams.scheduleNameSingle} and all its ${mainParams.timeslotNamePlural}?`}
                        </Typography>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={this.handleDeleteClose} color="primary">
                            Cancel
                        </Button>
                        <Button onClick={this.handleDelete} color="secondary">
                            Delete
                        </Button>
                    </DialogActions>
                </Dialog>
                <Dialog
                    open={clearAllOpen}
                    onClose={this.handleClearAllClose}
                >
                    <DialogTitle>Confirm Clear All</DialogTitle>
                    <DialogContent>
                    <Typography>Are you sure you want to clear all {mainParams.timeslotNamePlural} and {mainParams.scheduleNamePlural}?</Typography>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={this.handleClearAllClose} color="primary">
                            Cancel
                        </Button>
                        <Button onClick={this.handleClearAll} color="secondary">
                            Clear All
                        </Button>
                    </DialogActions>
                </Dialog>
                    <div>
                        <Grid container spacing={0.5} justifyContent="center" marginTop={2} padding="5px">
                            <Grid item xs={4}>
                                <Typography variant="h6" align="center" sx={{ backgroundColor: '#eaeff1', color: '#222', borderRadius: '5px' }}>Start Time</Typography>
                            </Grid>

                            <Grid item xs={4}>
                                <Typography variant="h6" align="center" sx={{ backgroundColor: '#eaeff1', color: '#222', borderRadius: '5px' }}>
                                {toggleView === 'Timeslots' && hasModes ? 'Mode' : mainParams.scheduleNameSingle}
                                </Typography>
                            </Grid>
                            <Grid item xs={2}>
                                <Typography variant="h6" align="center" sx={{ backgroundColor: '#eaeff1', color: '#222', borderRadius: '5px' }}>hrs</Typography>
                            </Grid>
                            <Grid item xs={2}>
                                <Typography variant="h6" align="center" sx={{ backgroundColor: '#eaeff1', color: '#222', borderRadius: '5px' }}>Action</Typography>
                            </Grid>
                            {currentPageSlots.length > 0 ? (
                                currentPageSlots.map((slot, index) => (
                                    //console.log("slot",slot),
                                    <React.Fragment key={index}>
                                    <Grid item xs={4} sx={{ 
                                        backgroundColor: slot.color,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        minHeight: '40px' // Adjust this value as needed
                                    }}>
                                        <Typography align="center">{this.formatDateTime(slot.startTime)}</Typography>
                                    </Grid>
                                    <Grid item xs={4} sx={{ 
                                        backgroundColor: slot.color,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        minHeight: '40px' // Adjust this value as needed
                                    }}>
                                        <Typography align="center">
                                            {
                                                toggleView === 'Timeslots'
                                                    ? hasModes
                                                        ? (slot.mode && slot.mode.type) || 'No Mode'
                                                        : slot.scheduleName
                                                    : slot.name
                                            }
                                        </Typography>
                                    </Grid>
                                    <Grid item xs={2} sx={{ 
                                        backgroundColor: slot.color,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        minHeight: '40px' // Adjust this value as needed
                                    }}>
                                        <Typography align="center">{slot.duration}</Typography>
                                    </Grid>
                                    <Grid item xs={2} sx={{ 
                                        backgroundColor: slot.color,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        minHeight: '40px' // Adjust this value as needed
                                    }}>
                                        <Box display="flex" justifyContent="space-between" width="100%">
                                            <Button
                                                variant="contained"
                                                sx={{
                                                    backgroundColor: '#FFC107',
                                                    color: '#FFFFFF',
                                                    minWidth: '48%',
                                                    width: '48%',
                                                    '&:hover': {
                                                        backgroundColor: '#FFA000'
                                                    }
                                                }}
                                                onClick={() => this.handleEditOpen(index)}
                                            >
                                                <EditIcon />
                                            </Button>
                                            <Button
                                                variant="contained"
                                                sx={{
                                                    backgroundColor: '#F44336',
                                                    color: '#FFFFFF',
                                                    minWidth: '48%',
                                                    width: '48%',
                                                    '&:hover': {
                                                        backgroundColor: '#D32F2F'
                                                    }
                                                }}
                                                onClick={() => this.handleDeleteOpen(index)}
                                            >
                                                <RemoveCircleIcon />
                                            </Button>
                                        </Box>
                                    </Grid>
                                </React.Fragment>
                                ))
                            ) : (
                                <Box>
                                    <Typography variant="h5">No {mainParams.timeslotNamePlural} scheduled</Typography>
                                </Box>
                            )}
                        </Grid>
                        <Box display="flex" justifyContent="center" alignItems="center" marginTop={2}>
                            <Button
                                variant="contained"
                                onClick={this.handlePreviousPage}
                                disabled={!isPageInputActive && currentPage === 0}
                                sx={{
                                    backgroundColor: isPageInputActive ? '#F44336' : '#000000',
                                    color: '#FFFFFF',
                                    marginRight: '10px',
                                    '&:hover': {
                                        backgroundColor: isPageInputActive ? '#D32F2F' : '#333333'
                                    }
                                }}
                            >
                                &lt;
                            </Button>
                            {isPageInputActive ? (
                                <TextField
                                    type="number"
                                    value={pageInputValue}
                                    onChange={this.handlePageInputChange}
                                    sx={{
                                        width: '60px',
                                    }}
                                    InputProps={{
                                        style: {
                                            height: '37px',
                                            padding: '0px',
                                            textAlign: 'center',
                                        }
                                    }}
                                    inputProps={{
                                        style: { textAlign: 'center' }
                                    }}
                                />
                            ) : (
                                <Button
                                    variant="contained"
                                    onClick={this.handlePageInputToggle}
                                    disabled={totalPages <= 1}
                                    sx={{
                                        backgroundColor: totalPages <= 1 ? '#333333' : '#000000',
                                        color: '#FFFFFF',
                                        height: '36px',
                                        '&:hover': {
                                            backgroundColor: '#333333'
                                        }
                                    }}
                                >
                                    {currentPage + 1}/{totalPages}
                                </Button>
                            )}
                            <Button
                                variant="contained"
                                onClick={isPageInputActive ? this.handleJumpToPage : this.handleNextPage}
                                disabled={!isPageInputActive && currentPage >= totalPages - 1}
                                sx={{
                                    backgroundColor: isPageInputActive ? '#2196F3' : '#000000',
                                    color: '#FFFFFF',
                                    marginLeft: '10px',
                                    '&:hover': {
                                        backgroundColor: isPageInputActive ? '#1976D2' : '#333333'
                                    }
                                }}
                            >
                                &gt;
                            </Button>
                        </Box>
                    </div>
            </Box>
        );
    }
}
