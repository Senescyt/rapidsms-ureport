######################
# Tag Cloud Settings #
######################
drop_words=['the','and','a','at','are','by','is','it','but','for','on','of','to','be','or','not',]

tag_cloud_size=40

######################
# Map Settings       #
######################

#set the overlay data urls
MAP_URLS = (
    # e.g ('Health Facilities', '/health_facilities'),
)

# set the overlay colors and icons
MAP_TYPES = {
    # e.g 'health_facilities': ['army.png', '#14740a'],
}

#base layer url
BASE_LAYER = ''

#map bounding box
min_lon = '29.55322265625'
max_lon = '33.92578125'
min_lat = '-1.0326589311777759'
max_lat = '4.280680030820496'

colors = ['#4572A7', '#AA4643', '#89A54E', '#80699B', '#3D96AE', '#DB843D', '#92A8CD', '#A47D7C', '#B5CA92']

AUTHENTICATED_TABS = [
    ("rapidsms.contrib.messagelog.views.message_log",       "Message Log"),
    ("polls",                                               "Polls"),
    ("poll_dashboard",                                    "Polls Dashboard"),
]
