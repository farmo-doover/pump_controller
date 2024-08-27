
import RemoteAccess from 'doover_home/RemoteAccess';
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, TextField, FormControl, FormLabel, RadioGroup, FormControlLabel, Radio, Box, InputAdornment, Grid, Typography, ToggleButtonGroup, ToggleButton } from '@mui/material';
import React, { Component } from 'react';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFnsV3';
import { addDays, addWeeks, format } from 'date-fns';

import RemoveCircleIcon from '@mui/icons-material/RemoveCircle';
import EditIcon from '@mui/icons-material/Edit';


const PAGE_SLOT_MAX = 10;

class TimeSlot {
    constructor(startTime, duration) {
        this.startTime = startTime;
        this.duration = duration;
    }
}

class Schedule {
    constructor(name, frequency) {
        this.name = name;
        this.frequency = frequency;
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
            toggleView: 'Timeslots',
            inSchedules: [],
        };
        this.updateUiStates = this.updateUiStates.bind(this);
    }

    handleClickOpen = () => {
        this.setState({ open: true, scheduleName: '' });
    };

    handleClose = () => {
        this.setState({ open: false });
    };

    handleEditOpen = (index) => {
        const slot = this.state.sortedTimeSlots[index];
        this.setState({
            editOpen: true,
            editIndex: index,
            startDate: slot.startTime,
            duration: slot.duration,
            editSchedule: slot.scheduleName
        });
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

    handleSave = () => {
        const { startDate, endDate, duration, frequency, scheduleName } = this.state;
        const name = frequency === 'once' ? 'Once' : scheduleName || 'Unnamed Schedule';
        const newSchedule = new Schedule(name, frequency);
    
        let timeslots = [];
    
        if (frequency === 'once') {
            const startEpoch = new Date(startDate).getTime() / 1000;
            const endEpoch = startEpoch + duration * 3600;
    
            newSchedule.addTimeSlot(new TimeSlot(startDate, duration));
            timeslots.push({
                "start_time": startEpoch,
                "end_time": endEpoch,
                "frequency": frequency,
                "schedule_id": 1
            });
        } else {
            let currentDate = new Date(startDate);
            let scheduleId = 1;
    
            while (currentDate <= endDate) {
                const startEpoch = new Date(currentDate).getTime() / 1000;
                const endEpoch = startEpoch + duration * 3600;
    
                newSchedule.addTimeSlot(new TimeSlot(new Date(currentDate), duration));
                timeslots.push({
                    "start_time": startEpoch,
                    "end_time": endEpoch,
                    "frequency": frequency,
                    "schedule_id": scheduleId
                });
    
                scheduleId++;
    
                if (frequency === 'daily') {
                    currentDate = addDays(currentDate, 1);
                } else if (frequency === 'weekly') {
                    currentDate = addWeeks(currentDate, 1);
                }
            }
        }
    
        const payload = [{
            "start_time": new Date(startDate).getTime() / 1000,
            "end_time": new Date(endDate).getTime() / 1000,
            "frequency": frequency,
            "schedule_name": scheduleName,
            "timeslots": timeslots
        }];
    
        const apiWrapper = window.dooverDataAPIWrapper;
        const agent_id = this.getUi().agent_key;
    
        apiWrapper.get_temp_token().then((token) => {
            apiWrapper.post_channel_aggregate(
                {
                    agent_id: agent_id,
                    channel_name: 'pump_schedules',
                },
                JSON.stringify(payload),  // Use JSON.stringify here to ensure proper JSON format
                token.token,
            );
        });
    
        this.setState((prevState) => ({
            schedules: [...prevState.schedules, newSchedule],
            open: false
        }), this.sortSchedules);
    };
    
    

    handleEditSave = () => {
        const { startDate, duration, editIndex, sortedTimeSlots } = this.state;
        const { scheduleName } = sortedTimeSlots[editIndex];
        const schedule = this.state.schedules.find(sch => sch.name === scheduleName);
        if (schedule) {
            const slotIndex = schedule.timeSlots.findIndex(slot => slot.startTime === sortedTimeSlots[editIndex].startTime);
            schedule.timeSlots[slotIndex] = new TimeSlot(startDate, duration);
            this.setState({
                schedules: [...this.state.schedules],
                editOpen: false
            }, this.sortSchedules);
        }
    };

    handleDelete = () => {
        const { deleteIndex, sortedTimeSlots } = this.state;
        const { scheduleName, startTime } = sortedTimeSlots[deleteIndex];
        const schedule = this.state.schedules.find(sch => sch.name === scheduleName);

        if (schedule) {
            const slotIndex = schedule.timeSlots.findIndex(slot => slot.startTime === startTime);
            schedule.removeTimeSlot(slotIndex);

            if (schedule.isEmpty()) {
                this.setState((prevState) => ({
                    schedules: prevState.schedules.filter(sch => sch.name !== scheduleName),
                    deleteOpen: false
                }), this.sortSchedules);
            } else {
                this.setState({
                    schedules: [...this.state.schedules],
                    deleteOpen: false
                }, this.sortSchedules);
            }
        }
    };

    handleClearAll = () => {
        this.setState({
            schedules: [],
            currentPage: 0,
            sortedTimeSlots: [],
            clearAllOpen: false
        });
    };

    sortSchedules = () => {
        const allTimeSlots = this.state.schedules.flatMap(schedule => 
            schedule.timeSlots.map(slot => ({
                ...slot,
                scheduleName: schedule.name
            }))
        );
        allTimeSlots.sort((a, b) => a.startTime - b.startTime);

        this.setState({ sortedTimeSlots: allTimeSlots });
    };

    formatDateTime = (date) => {
        return format(date, 'dd/M/yy h:mma');
    };

    getCurrentPageTimeSlots = () => {
        const { sortedTimeSlots, currentPage } = this.state;
        const startIndex = currentPage * PAGE_SLOT_MAX;
        const endIndex = startIndex + PAGE_SLOT_MAX;
        return sortedTimeSlots.slice(startIndex, endIndex);
    };

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
        console.logf("current state", this.state);
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
                    channel_name: "pump_schedules",
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
                console.log('test:', test);
                
                // Convert the test data back into the original structure
                const schedules = test.map((scheduleData) => {
                    const { start_time, end_time, frequency, schedule_name, timeslots } = scheduleData;
    
                    // Create a new Schedule object
                    const schedule = new Schedule(schedule_name, frequency);
    
                    // Process each timeslot
                    timeslots.forEach((timeslot) => {
                        const { start_time: tsStartTime, end_time: tsEndTime, schedule_id } = timeslot;
                        const duration = (tsEndTime - tsStartTime) / 3600; // Convert end_time back to duration in hours
                        
                        // Add the timeslot to the schedule
                        schedule.addTimeSlot(new TimeSlot(new Date(tsStartTime * 1000), duration));
                    });
    
                    return schedule;
                });
                console.log('schedules:', schedules);
                // Update the state with the new schedules
                this.setState({ schedules }, this.sortSchedules);
            })
            .catch((err) => {
                console.error('ERROR:', err);
            });
    }
    
    


    render() {

        console.log("state", this.state);

        const { currentPage, isPageInputActive, pageInputValue, frequency, sortedTimeSlots, deleteOpen, clearAllOpen, toggleView } = this.state;
        const currentPageTimeSlots = this.getCurrentPageTimeSlots();
        const totalPages = Math.ceil(sortedTimeSlots.length / PAGE_SLOT_MAX);

        return (
            <Box>
                <Box display="flex" justifyContent="space-between" alignItems="center" position="relative" >
                    <Button variant="contained" color="primary" onClick={this.handleClickOpen} sx={{height:"50px", margin:"0px"}}>
                        Create Schedule
                    </Button>
                    <ToggleButtonGroup
                        value={toggleView}
                        exclusive
                        onChange={(event, newView) => this.setState({ toggleView: newView || toggleView })}
                          
                        sx={{ height:"50px" }}
                    >
                        <ToggleButton value="Schedules" sx={{ textTransform: 'none' }}>Schedules</ToggleButton>
                        <ToggleButton value="Timeslots" sx={{ textTransform: 'none' }}>Timeslots</ToggleButton>
                    </ToggleButtonGroup>
                    {sortedTimeSlots.length > 0 && (
                        <Button
                            variant="contained"
                            color="secondary"
                            onClick={this.handleClearAllOpen}
                            sx={{
                                height:"50px",
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
                                <Box display="flex" alignItems="center" marginTop={2}>
                                    <FormControl margin="normal" sx={{ flex: '0 1 auto', marginLeft: '20px' }}>
                                        <FormLabel component="legend" sx={{ color: '#000000' }}>Repeat until:</FormLabel>
                                        <LocalizationProvider dateAdapter={AdapterDateFns}>
                                            <DateTimePicker
                                                value={this.state.endDate}
                                                onChange={this.handleEndDateChange}
                                                renderInput={(params) => <TextField {...params} fullWidth margin="normal" />}
                                            />
                                        </LocalizationProvider>
                                    </FormControl>
                                </Box>
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
                    <DialogTitle>Edit Time Slot</DialogTitle>
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
                        <Typography>Are you sure you want to delete this TimeSlot?</Typography>
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
                {currentPageTimeSlots.length > 0 ? (
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
                        {currentPageTimeSlots.map((slot, index) => (
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
                                            <EditIcon/>
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
                                            <RemoveCircleIcon/>
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
                ) : (<center><h3>Nothing Scheduled</h3></center>)}
            </Box>
        );
    }
}
