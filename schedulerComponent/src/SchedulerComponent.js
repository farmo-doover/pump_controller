import RemoteAccess from 'doover_home/RemoteAccess';
import {
    Button, Dialog, DialogActions, DialogContent, DialogTitle, TextField,
    FormControl, FormLabel, RadioGroup, FormControlLabel, Radio, Box,
    InputAdornment, Grid, Typography, ToggleButtonGroup, ToggleButton
} from '@mui/material';
import React, { Component } from 'react';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFnsV3';
import { addDays, addWeeks, format } from 'date-fns';

import RemoveCircleIcon from '@mui/icons-material/RemoveCircle';
import EditIcon from '@mui/icons-material/Edit';

const PAGE_SLOT_MAX = 10;

class TimeSlot {
    constructor(startTime, duration, edited = 0) {
        this.startTime = startTime;
        this.duration = duration;
        this.edited = edited;
    }
}

class Schedule {
    constructor(name, frequency, startTime, endTime, duration) {
        this.name = name;
        this.frequency = frequency;
        this.startTime = startTime;
        this.endTime = endTime;
        this.duration = duration;
        this.timeSlots = [];
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
            startDate: new Date(),
            endDate: new Date(),
            duration: 1,
            frequency: 'once',
            scheduleName: '',
            schedules: [],
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
            endDate: new Date(roundedDate.getTime() + 60 * 60 * 1000), // Default end time is 1 hour after start time
            duration: 1,
            frequency: 'once'
        });
    };

    handleClose = () => {
        this.setState({ open: false, startDateError: "", endDateError: ""  });
    };

    handleEditOpen = (index) => {
        const { toggleView, sortedTimeSlots, sortedSchedules } = this.state;
        
        if (toggleView === 'Timeslots') {
            const slot = sortedTimeSlots[index];
            if (slot) {
                this.setState({
                    editOpen: true,
                    editIndex: index,
                    startDate: new Date(slot.startTime),
                    duration: slot.duration,
                    editSchedule: slot.scheduleName,
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
                    editSchedule: schedule.scheduleName,
                    editFrequency: schedule.frequency,
                    editingSchedule: true
                });
            }
        }
    };

    handleEditFrequencyChange = (event) => {
        this.setState({ editFrequency: event.target.value });
    };

    handleEditClose = () => {
        this.setState({ editOpen: false });
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

    pushChanges = () => {
        const payload = this.state.schedules.length > 0 ? this.state.schedules.map(schedule => {
            return {
                schedule_name: schedule.name,
                frequency: schedule.frequency,
                start_time: new Date(schedule.startTime).getTime() / 1000,
                end_time: new Date(schedule.endTime).getTime() / 1000,
                duration: schedule.duration,
                timeslots: schedule.timeSlots.map(slot => ({
                    start_time: new Date(slot.startTime).getTime() / 1000,
                    end_time: new Date(slot.startTime).getTime() / 1000 + slot.duration * 3600,
                    duration: slot.duration,
                    edited: slot.edited
                }))
            };
        }) : []; // If there are no schedules, send an empty array
    
        const apiWrapper = window.dooverDataAPIWrapper;
        const agent_id = this.getUi().agent_key;
    
        apiWrapper.get_temp_token().then((token) => {
            apiWrapper.post_channel_aggregate(
                {
                    agent_id: agent_id,
                    channel_name: 'schedules',
                },
                JSON.stringify(payload),
                token.token,
            );
        });
    };

    createTimeslot = (startTime, duration, edited = 0) => {
        return new TimeSlot(new Date(startTime), duration, edited);
    };

    handleSave = () => {
        const { startDate, endDate, duration, frequency, scheduleName } = this.state;
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
    
        const name = frequency === 'once' ? 'Once' : scheduleName || 'Unnamed Schedule';
        const newSchedule = new Schedule(name, frequency, startDate, endDate, duration);
    
        if (frequency === 'once') {
            newSchedule.addTimeSlot(new TimeSlot(startDate, duration, 0));
        } else {
            let currentDate = new Date(startDate);
            while (currentDate <= endDate) {
                newSchedule.addTimeSlot(new TimeSlot(new Date(currentDate), duration, 0));
                if (frequency === 'daily') {
                    currentDate = addDays(currentDate, 1);
                } else if (frequency === 'weekly') {
                    currentDate = addWeeks(currentDate, 1);
                }
            }
        }
    
        this.setState((prevState) => ({
            schedules: [...prevState.schedules, newSchedule],
            open: false
        }), () => {
            this.sortSchedules();
            this.pushChanges();
        });
    };

    updateTimeslots = (schedule, newStartTime, newEndTime, newDuration, newFrequency) => {
        let updatedTimeslots = [];
        const oldFrequency = schedule.frequency;
    
        if (newFrequency === 'once') {
            const editedSlot = schedule.timeSlots.find(slot => slot.edited === 1);
            if (editedSlot) {
                updatedTimeslots = [new TimeSlot(editedSlot.startTime, editedSlot.duration, 1)];
            } else {
                updatedTimeslots = [new TimeSlot(newStartTime, newDuration, 0)];
            }
        } else {
            let currentTime = new Date(newStartTime);
            while (currentTime <= newEndTime) {
                const existingSlot = schedule.timeSlots.find(slot => 
                    slot.startTime.getTime() === currentTime.getTime()
                );
    
                if (existingSlot && existingSlot.edited === 1) {
                    updatedTimeslots.push(new TimeSlot(existingSlot.startTime, existingSlot.duration, 1));
                } else {
                    updatedTimeslots.push(new TimeSlot(new Date(currentTime), newDuration, 0));
                }
    
                if (newFrequency === 'daily') {
                    currentTime = addDays(currentTime, 1);
                } else if (newFrequency === 'weekly') {
                    currentTime = addWeeks(currentTime, 1);
                }
            }
        }
    
        schedule.timeSlots.forEach(slot => {
            if (slot.edited === 1 && !updatedTimeslots.some(updatedSlot => 
                updatedSlot.startTime.getTime() === slot.startTime.getTime()
            )) {
                updatedTimeslots.push(new TimeSlot(slot.startTime, slot.duration, 1));
            }
        });
    
        updatedTimeslots.sort((a, b) => a.startTime - b.startTime);
    
        return updatedTimeslots;
    };

    handleEditSave = () => {
        const { startDate, endDate, duration, editIndex, sortedTimeSlots, sortedSchedules, toggleView, editFrequency } = this.state;
    
        if (toggleView === 'Timeslots') {
            const timeSlot = sortedTimeSlots[editIndex];
            if (timeSlot) {
                this.setState(prevState => {
                    const updatedSchedules = prevState.schedules.map(schedule => {
                        if (schedule.name === timeSlot.scheduleName) {
                            const updatedTimeSlots = schedule.timeSlots.map(slot => 
                                slot.startTime.getTime() === timeSlot.startTime.getTime()
                                    ? new TimeSlot(new Date(startDate), duration, 1)  // Set edited to 1
                                    : slot
                            );
                            return { ...schedule, timeSlots: updatedTimeSlots };
                        }
                        return schedule;
                    });
                    return { schedules: updatedSchedules, editOpen: false };
                }, () => {
                    this.sortSchedules();
                    this.pushChanges();
                });
            }
        } else {
            const scheduleToEdit = sortedSchedules[editIndex];
            if (scheduleToEdit) {
                this.setState(prevState => {
                    const updatedSchedules = prevState.schedules.map(schedule => {
                        if (schedule.name === scheduleToEdit.scheduleName) {
                            const updatedTimeslots = this.updateTimeslots(
                                schedule, 
                                startDate, 
                                endDate, 
                                duration, 
                                editFrequency
                            );
                            return {
                                ...schedule,
                                startTime: startDate,
                                endTime: endDate,
                                duration: duration,
                                frequency: editFrequency,
                                timeSlots: updatedTimeslots
                            };
                        }
                        return schedule;
                    });
                    return { 
                        schedules: updatedSchedules, 
                        editOpen: false 
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
            const scheduleIndex = this.state.schedules.findIndex(sch => sch.name === scheduleName);
    
            if (scheduleIndex !== -1) {
                const updatedSchedules = [...this.state.schedules];
                const schedule = updatedSchedules[scheduleIndex];
                const slotIndex = schedule.timeSlots.findIndex(slot => slot.startTime.getTime() === startTime.getTime());
    
                schedule.removeTimeSlot(slotIndex);
    
                if (schedule.isEmpty()) {
                    updatedSchedules.splice(scheduleIndex, 1);
                }
    
                this.setState({
                    schedules: updatedSchedules,
                    deleteOpen: false
                }, () => {
                    this.sortSchedules();
                    this.pushChanges();
                });
            }
        } else if (toggleView === 'Schedules') {
            const scheduleToDelete = sortedSchedules[deleteIndex];
            this.setState((prevState) => ({
                schedules: prevState.schedules.filter(schedule => schedule.name !== scheduleToDelete.scheduleName),
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

    sortSchedules = () => {
        const allTimeSlots = this.state.schedules.flatMap(schedule =>
            schedule.timeSlots.map(slot => ({
                ...slot,
                scheduleName: schedule.name || 'Unnamed Schedule'
            }))
        );
        allTimeSlots.sort((a, b) => new Date(a.startTime) - new Date(b.startTime));
    
        const allSchedules = this.state.schedules.map(schedule => ({
            scheduleName: schedule.name || 'Unnamed Schedule',
            frequency: schedule.frequency || 'once',
            startTime: new Date(schedule.startTime),
            endTime: new Date(schedule.endTime),
            duration: schedule.duration || 0,
        }));
        allSchedules.sort((a, b) => a.startTime - b.startTime);
    
        this.setState({ 
            sortedTimeSlots: allTimeSlots,
            sortedSchedules: allSchedules
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

    componentDidMount() {
        this.updateUiStates()
            .then((test) => {
                const schedules = test.map((scheduleData) => {
                    const { start_time, end_time, frequency, schedule_name, timeslots, duration } = scheduleData;
    
                    const schedule = new Schedule(
                        schedule_name,
                        frequency,
                        new Date(start_time * 1000),
                        new Date(end_time * 1000), 
                        duration
                    );
    
                    timeslots.forEach((timeslot) => {
                        const { start_time: tsStartTime, end_time: tsEndTime, edited } = timeslot;
                        const slotDuration = (tsEndTime - tsStartTime) / 3600;
    
                        schedule.addTimeSlot(new TimeSlot(
                            new Date(tsStartTime * 1000), 
                            slotDuration,
                            edited || 0 
                        ));
                    });
    
                    return schedule;
                });
    
                this.setState({ schedules }, this.sortSchedules);
            })
            .catch((err) => {
                console.error('ERROR:', err);
            });
    }

    render() {


        const { currentPage, isPageInputActive, pageInputValue, frequency, sortedTimeSlots, sortedSchedules, deleteOpen, clearAllOpen, toggleView } = this.state;
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
                        Create Schedule
                    </Button>
                    <ToggleButtonGroup
                        value={toggleView}
                        exclusive
                        onChange={(event, newView) => this.setState({ toggleView: newView || toggleView })}
                        sx={{ height: "50px" }}
                    >
                        <ToggleButton value="Schedules" sx={{ textTransform: 'none' }}>Schedules</ToggleButton>
                        <ToggleButton value="Timeslots" sx={{ textTransform: 'none' }}>Timeslots</ToggleButton>
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
                    <DialogTitle>Create Schedule</DialogTitle>
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
                    <DialogTitle>{this.state.editingSchedule ? 'Edit Schedule' : 'Edit Time Slot'}</DialogTitle>
                    <DialogContent>
                        <FormControl fullWidth margin="normal">
                            <FormLabel component="legend">Start Date/Time</FormLabel>
                            <LocalizationProvider dateAdapter={AdapterDateFns}>
                                <DateTimePicker
                                    value={this.state.startDate}
                                    onChange={this.handleDateChange}
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
                                        onChange={this.handleEditFrequencyChange}
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
                                                onChange={this.handleEndDateChange}
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
                                onChange={this.handleDurationChange}
                                InputProps={{
                                    endAdornment: <InputAdornment position="end">hrs</InputAdornment>,
                                }}
                            />
                        </FormControl>
                    </DialogContent>
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
                                ? "Are you sure you want to delete this TimeSlot?"
                                : "Are you sure you want to delete this Schedule and all its TimeSlots?"}
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
                        <Typography>Are you sure you want to clear all TimeSlots and Schedules?</Typography>
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
                {currentPageSlots.length > 0 ? (
                    <div>
                        <Grid container spacing={0.5} justifyContent="center" marginTop={2} padding="5px">
                            <Grid item xs={4}>
                                <Typography variant="h6" align="center" sx={{ backgroundColor: '#eaeff1', color: '#222', borderRadius: '5px' }}>Start Time</Typography>
                            </Grid>

                            <Grid item xs={4}>
                                <Typography variant="h6" align="center" sx={{ backgroundColor: '#eaeff1', color: '#222', borderRadius: '5px' }}>Schedule</Typography>
                            </Grid>
                            <Grid item xs={2}>
                                <Typography variant="h6" align="center" sx={{ backgroundColor: '#eaeff1', color: '#222', borderRadius: '5px' }}>hrs</Typography>
                            </Grid>
                            <Grid item xs={2}>
                                <Typography variant="h6" align="center" sx={{ backgroundColor: '#eaeff1', color: '#222', borderRadius: '5px' }}>Action</Typography>
                            </Grid>

                            {currentPageSlots.map((slot, index) => (
                                <React.Fragment key={index}>
                                    <Grid item xs={4}>
                                        <Typography align="center">{this.formatDateTime(slot.startTime)}</Typography>
                                    </Grid>
                                    <Grid item xs={4}>
                                        <Typography align="center">{slot.scheduleName}</Typography>
                                    </Grid>
                                    <Grid item xs={2}>
                                        <Typography align="center">{slot.duration}</Typography>
                                    </Grid>
                                    <Grid item xs={2}>
                                        <Box display="flex" justifyContent="space-between">
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
                            ))}
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
                ) : (
                    <Box>
                        <Typography variant="h5">No events scheduled</Typography>
                    </Box>
                )}
            </Box>
        );
    }
}
