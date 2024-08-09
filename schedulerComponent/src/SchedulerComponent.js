import RemoteAccess from 'doover_home/RemoteAccess';
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, TextField, FormControl, FormLabel, RadioGroup, FormControlLabel, Radio, Box, InputAdornment, Grid, Typography } from '@mui/material';
import React, { Component } from 'react';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFnsV3';
import { addDays, addWeeks, format } from 'date-fns';

import RemoveCircleIcon from '@mui/icons-material/RemoveCircle';
import EditIcon from '@mui/icons-material/Edit';

const PAGE_SLOT_MAX = 15;

class TimeSlot {
    constructor(startTime, duration) {
        this.startTime = startTime;
        this.duration = duration;
    }
}

export default class RemoteComponent extends RemoteAccess {
    constructor(props) {
        super(props);
        this.state = {
            open: false,
            editOpen: false,
            editIndex: -1,
            startDate: new Date(),
            endDate: new Date(),
            duration: 1,
            frequency: 'once',
            timeSlots: [],
            currentPage: 0,
            isPageInputActive: false,
            pageInputValue: ''
        };
    }

    handleClickOpen = () => {
        this.setState({ open: true });
    };

    handleClose = () => {
        this.setState({ open: false });
    };

    handleEditOpen = (index) => {
        const slot = this.state.timeSlots[index];
        this.setState({
            editOpen: true,
            editIndex: index,
            startDate: slot.startTime,
            duration: slot.duration
        });
    };

    handleEditClose = () => {
        this.setState({ editOpen: false });
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

    handleSave = () => {
        const { startDate, endDate, duration, frequency } = this.state;

        if (frequency === 'once') {
            const newTimeSlot = new TimeSlot(startDate, duration);
            this.setState((prevState) => ({
                timeSlots: [...prevState.timeSlots, newTimeSlot],
                open: false
            }), this.sortTimeSlots);
        } else {
            const newTimeSlots = [];
            let currentDate = new Date(startDate);

            while (currentDate <= endDate) {
                newTimeSlots.push(new TimeSlot(new Date(currentDate), duration));
                if (frequency === 'daily') {
                    currentDate = addDays(currentDate, 1);
                } else if (frequency === 'weekly') {
                    currentDate = addWeeks(currentDate, 1);
                }
            }

            this.setState((prevState) => ({
                timeSlots: [...prevState.timeSlots, ...newTimeSlots],
                open: false
            }), this.sortTimeSlots);
        }
    };

    handleEditSave = () => {
        const { startDate, duration, editIndex, timeSlots } = this.state;
        const updatedTimeSlots = [...timeSlots];
        updatedTimeSlots[editIndex] = new TimeSlot(startDate, duration);
        this.setState({
            timeSlots: updatedTimeSlots,
            editOpen: false
        }, this.sortTimeSlots);
    };

    handleDelete = (index) => {
        this.setState((prevState) => ({
            timeSlots: prevState.timeSlots.filter((_, i) => i !== index)
        }));
    };

    handleClearSchedule = () => {
        this.setState({
            timeSlots: [],
            currentPage: 0
        });
    };

    sortTimeSlots = () => {
        this.setState((prevState) => ({
            timeSlots: prevState.timeSlots.slice().sort((a, b) => a.startTime - b.startTime)
        }));
    };

    formatDateTime = (date) => {
        return format(date, 'eee dd MMM hh:mm aa');
        // return format(date, 'dd/MM hh:mm aa');
    };

    getCurrentPageTimeSlots = () => {
        const { timeSlots, currentPage } = this.state;
        const startIndex = currentPage * PAGE_SLOT_MAX;
        const endIndex = startIndex + PAGE_SLOT_MAX;
        return timeSlots.slice(startIndex, endIndex);
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
    };

    handlePageInputChange = (event) => {
        this.setState({ pageInputValue: event.target.value });
    };

    handleJumpToPage = () => {
        const { pageInputValue, timeSlots } = this.state;
        const totalPages = Math.ceil(timeSlots.length / PAGE_SLOT_MAX);
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

    render() {
        const { currentPage, timeSlots, isPageInputActive, pageInputValue } = this.state;
        const totalPages = Math.ceil(timeSlots.length / PAGE_SLOT_MAX);
        const currentPageTimeSlots = this.getCurrentPageTimeSlots();

        return (
            <Box>
                <Box display="flex" justifyContent="space-around" alignItems="center" position="relative" marginTop="10px" marginBottom="15px">
                    <Button variant="contained" color="primary" onClick={this.handleClickOpen}>
                        Add Schedule
                    </Button>
                    {timeSlots.length > 0 && (
                        <Button
                            variant="contained"
                            color="secondary"
                            onClick={this.handleClearSchedule}
                            sx={{
                                // position: 'absolute',
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
                            {this.state.frequency !== 'once' && (
                                <FormControl margin="normal" sx={{ flex: '0 1 auto', marginLeft: '20px' }}>
                                    <FormLabel component="legend" sx={{ color: '#000000' }}>Repeat Until</FormLabel>
                                    <LocalizationProvider dateAdapter={AdapterDateFns}>
                                        <DateTimePicker
                                            value={this.state.endDate}
                                            onChange={this.handleEndDateChange}
                                            renderInput={(params) => <TextField {...params} fullWidth margin="normal" />}
                                        />
                                    </LocalizationProvider>
                                </FormControl>
                            )}
                        </Box>
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
                {timeSlots.length > 0 ? (
                    <div>
                    <Grid container spacing={0.5} justifyContent="center" marginTop={2} padding="5px">
                        <Grid item xs={6}>
                            {/* <Typography variant="h6" align="center" sx={{ backgroundColor: '#000000', color: '#FFFFFF' }}>Start Time</Typography> */}
                            <Typography variant="h6" align="center" sx={{ backgroundColor: '#eaeff1', color: '#222', borderRadius: '5px' }}>Start Time</Typography>
                        </Grid>
                        <Grid item xs={3}>
                            {/* <Typography variant="h6" align="center" sx={{ backgroundColor: '#000000', color: '#FFFFFF' }}>Duration</Typography> */}
                            <Typography variant="h6" align="center" sx={{ backgroundColor: '#eaeff1', color: '#222', borderRadius: '5px' }}>Duration</Typography>
                        </Grid>
                        <Grid item xs={3}>
                            {/* <Typography variant="h6" align="center" sx={{ backgroundColor: '#000000', color: '#FFFFFF' }}>Action</Typography> */}
                            <Typography variant="h6" align="center" sx={{ backgroundColor: '#eaeff1', color: '#222', borderRadius: '5px' }}>Action</Typography>
                        </Grid>
                        {currentPageTimeSlots.map((slot, index) => (
                            <React.Fragment key={index}>
                                <Grid item xs={6}>
                                    <Typography align="center">{this.formatDateTime(slot.startTime)}</Typography>
                                </Grid>
                                <Grid item xs={3}>
                                    <Typography align="center">{slot.duration} hrs</Typography>
                                </Grid>
                                <Grid item xs={3}>
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
                                            onClick={() => this.handleDelete(index)}
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
