# FAFO Windows

Windows-only tools. Each folder is its own app, with its own server and its own start file. They do not import each other.

The launcher in `launcher/` can add or remove one tool. It will not do either unless the request includes `"confirm": true`.

Ready in this pass: Disk Space, Reports and Logs, Event Viewer, PC Health, Startup List. These read the PC. They do not delete files, clear logs, or turn startup programs off.
