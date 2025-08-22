// frontend/src/integrations/hubspot.js

import { useState, useEffect } from 'react';
import {
    Box,
    Button,
    CircularProgress
} from '@mui/material';
import axios from 'axios';

export const HubspotIntegration = ({ user, org, integrationParams, setIntegrationParams }) => {
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);

    // This function is called when the 'Connect' button is clicked
    const handleConnectClick = async () => {
        try {
            setIsConnecting(true);
            const formData = new FormData();
            formData.append('user_id', user);
            formData.append('org_id', org);
            
            // 1. Call our backend's /authorize endpoint
            const response = await axios.post(`http://localhost:8000/integrations/hubspot/authorize`, formData);
            const authURL = response?.data;

            // 2. Open the authorization URL from the backend in a popup window
            const newWindow = window.open(authURL, 'HubSpot Authorization', 'width=600, height=800');

            // 3. Check every 200ms to see if the popup window has been closed
            const pollTimer = window.setInterval(() => {
                if (newWindow?.closed !== false) { 
                    window.clearInterval(pollTimer);
                    handleWindowClosed(); // If it's closed, check if we got the credentials
                }
            }, 200);
        } catch (e) {
            setIsConnecting(false);
            alert(e?.response?.data?.detail);
        }
    }

    // This function runs after the popup window is closed
    const handleWindowClosed = async () => {
        try {
            const formData = new FormData();
            formData.append('user_id', user);
            formData.append('org_id', org);

            // 4. Call our backend's /credentials endpoint to get the token
            const response = await axios.post(`http://localhost:8000/integrations/hubspot/credentials`, formData);
            const credentials = response.data; 
            
            // 5. If we successfully got credentials, update the UI to a "Connected" state
            if (credentials) {
                setIsConnecting(false);
                setIsConnected(true);
                setIntegrationParams(prev => ({ ...prev, credentials: credentials, type: 'HubSpot' }));
            } else {
                setIsConnecting(false);
            }
        } catch (e) {
            setIsConnecting(false);
            // This is expected if the user closes the window without finishing
            console.log("Auth not completed.");
        }
    }

    useEffect(() => {
        setIsConnected(integrationParams?.credentials && integrationParams?.type === 'HubSpot' ? true : false);
    }, [integrationParams]);

    return (
        <>
        <Box sx={{mt: 2}}>
            Parameters
            <Box display='flex' alignItems='center' justifyContent='center' sx={{mt: 2}}>
                <Button 
                    variant='contained' 
                    onClick={isConnected ? () => {} : handleConnectClick}
                    color={isConnected ? 'success' : 'primary'}
                    disabled={isConnecting}
                    style={{
                        pointerEvents: isConnected ? 'none' : 'auto',
                        cursor: isConnected ? 'default' : 'pointer',
                    }}
                >
                    {isConnected ? 'HubSpot Connected' : isConnecting ? <CircularProgress size={24} color="inherit" /> : 'Connect to HubSpot'}
                </Button>
            </Box>
        </Box>
      </>
    );
}