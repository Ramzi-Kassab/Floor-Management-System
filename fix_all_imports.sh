#!/bin/bash

# Fix hiring module
sed -i 's/Application/JobApplication/g; s/\bOffer\b/JobOffer/g' floor_app/operations/hiring/views.py

# Fix hoc module
sed -i 's/HOCObservation/HazardObservation/g; s/HOCCategory/HazardCategory/g; s/HOCAction/HOCComment/g' floor_app/operations/hoc/views.py

# Fix meetings module
sed -i 's/\bMeeting\b/MorningMeeting/g; s/MeetingAttendee/MorningMeetingAttendance/g' floor_app/operations/meetings/views.py

# Fix journey_management module
sed -i 's/\bJourney\b/JourneyPlan/g; s/JourneyCheckpoint/JourneyCheckIn/g' floor_app/operations/journey_management/views.py

# Fix user_preferences module
sed -i 's/UserDashboardWidget/SavedView/g' floor_app/operations/user_preferences/views.py

# Fix utility_tools module
sed -i 's/Calculator/ToolUsageLog/g; s/FileConversion/SavedConversion/g' floor_app/operations/utility_tools/views.py

# Fix vendor_portal module
sed -i 's/VendorContact/VendorCommunication/g; s/VendorOrder/PurchaseOrder/g; s/VendorInvoice/VendorPerformanceReview/g; s/VendorDocument/VendorCommunication/g; s/VendorRating/VendorPerformanceReview/g' floor_app/operations/vendor_portal/views.py

echo "All model name fixes applied!"
