import RemoteAccess from 'doover_home/RemoteAccess';
import { ThemeProvider } from '@mui/material/styles';
import React, { Component } from 'react';


export default class RemoteComponent extends RemoteAccess {
    constructor(props) {
        super(props);
    }

    render() {
        return (
            <ThemeProvider theme={this.getTheme()}>
                <h2>Remote Component Here</h2>
            </ThemeProvider>
        );
    }
}
