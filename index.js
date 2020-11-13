/**
    Application example written in NodeJS.
    Shows the device name and serial number with a timestamp every second.
    Author: RECORD EVOLUTION GmbH
*/
'use strict';

// Constants
const PORT = 8000;
const HOST = process.env.DEVICE_NAME + '';

console.log(`Running on http://${HOST}:${PORT}`);
console.log(' -- Device:', process.env.DEVICE_NAME, 'Serial Number:', process.env.DEVICE_SERIAL_NUMBER);

setInterval(() => {
    console.log(' Hey Testing Reswarm @', new Date())
    console.log(' -- Device:', process.env.DEVICE_NAME, 'Serial Number:', process.env.DEVICE_SERIAL_NUMBER);
}, 1000);
