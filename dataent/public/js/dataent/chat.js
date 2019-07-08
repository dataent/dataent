// Dataent Chat
// Author - Achilles Rasquinha <achilles@epaas.xyz>

import Fuse   from 'fuse.js'
import hyper  from '../lib/hyper.min'

import './socketio_client'

import './ui/dialog'
import './ui/capture'

import './misc/user'

/* eslint semi: "never" */
// Fuck semicolons - https://mislav.net/2010/05/semicolons

// dataent extensions

/**
 * @description The base class for all Dataent Errors.
 *
 * @example
 * try
 *      throw new dataent.Error("foobar")
 * catch (e)
 *      console.log(e.name)
 * // returns "DataentError"
 *
 * @see  https://stackoverflow.com/a/32749533
 * @todo Requires "transform-builtin-extend" for Babel 6
 */
dataent.Error = Error
// class extends Error {
// 	constructor (message) {
// 		super (message)

// 		this.name = 'DataentError'

// 		if ( typeof Error.captureStackTrace === 'function' )
// 			Error.captureStackTrace(this, this.constructor)
// 		else
// 			this.stack = (new Error(message)).stack
// 	}
// }

/**
 * @description TypeError
 */
dataent.TypeError  = TypeError
// class extends dataent.Error {
// 	constructor (message) {
// 		super (message)

// 		this.name = this.constructor.name
// 	}
// }

/**
 * @description ValueError
 */
dataent.ValueError = Error
// class extends dataent.Error {
// 	constructor (message) {
// 		super (message)

// 		this.name = this.constructor.name
// 	}
// }

/**
 * @description ImportError
 */
dataent.ImportError = Error
// class extends dataent.Error {
// 	constructor (message) {
// 		super (message)

// 		this.name  = this.constructor.name
// 	}
// }

// dataent.datetime
dataent.provide('dataent.datetime')

/**
 * @description Dataent's datetime object. (Inspired by Python's datetime object).
 *
 * @example
 * const datetime = new dataent.datetime.datetime()
 */
dataent.datetime.datetime = class {
	/**
	 * @description Dataent's datetime Class's constructor.
	 */
	constructor (instance, format = null) {
		if ( typeof moment === undefined )
			throw new dataent.ImportError(`Moment.js not installed.`)

		this.moment      = instance ? moment(instance, format) : moment()
	}

	/**
	 * @description Returns a formatted string of the datetime object.
	 */
	format (format = null) {
		const  formatted = this.moment.format(format)
		return formatted
	}
}

/**
 * @description Dataent's daterange object.
 *
 * @example
 * const range = new dataent.datetime.range(dataent.datetime.now(), dataent.datetime.now())
 * range.contains(dataent.datetime.now())
 */
dataent.datetime.range   = class {
	constructor (start, end) {
		if ( typeof moment === undefined )
			throw new dataent.ImportError(`Moment.js not installed.`)

		this.start = start
		this.end   = end
	}

	contains (datetime) {
		const  contains = datetime.moment.isBetween(this.start.moment, this.end.moment)
		return contains
	}
}

/**
 * @description Returns the current datetime.
 *
 * @example
 * const datetime = new dataent.datetime.now()
 */
dataent.datetime.now   = () => new dataent.datetime.datetime()

dataent.datetime.equal = (a, b, type) => {
	a = a.moment
	b = b.moment

	const equal = a.isSame(b, type)

	return equal
}

/**
 * @description Compares two dataent.datetime.datetime objects.
 *
 * @param   {dataent.datetime.datetime} a - A dataent.datetime.datetime/moment object.
 * @param   {dataent.datetime.datetime} b - A dataent.datetime.datetime/moment object.
 *
 * @returns {number} 0 (if a and b are equal), 1 (if a is before b), -1 (if a is after b).
 *
 * @example
 * dataent.datetime.compare(dataent.datetime.now(), dataent.datetime.now())
 * // returns 0
 * const then = dataent.datetime.now()
 *
 * dataent.datetime.compare(then, dataent.datetime.now())
 * // returns 1
 */
dataent.datetime.compare = (a, b) => {
	a = a.moment
	b = b.moment

	if ( a.isBefore(b) )
		return  1
	else
	if ( b.isBefore(a) )
		return -1
	else
		return  0
}

// dataent.quick_edit
dataent.quick_edit      = (doctype, docname, fn) => {
	return new Promise(resolve => {
		dataent.model.with_doctype(doctype, () => {
			dataent.db.get_doc(doctype, docname).then(doc  => {
				const meta     = dataent.get_meta(doctype)
				const fields   = meta.fields
				const required = fields.filter(f => f.reqd || f.bold && !f.read_only)

				required.map(f => {
					if(f.fieldname == 'content' && doc.type == 'File') {
						f['read_only'] = 1;
					}
				})

				const dialog   = new dataent.ui.Dialog({
					 title: __(`Edit ${doctype} (${docname})`),
					fields: required,
					action: {
						primary: {
							   label: __("Save"),
							onsubmit: (values) => {
								dataent.call('dataent.client.save',
									{ doc: { doctype: doctype, docname: docname, ...doc, ...values } })
									  .then(r => {
										if ( fn )
											fn(r.message)

										resolve(r.message)
									  })

								dialog.hide()
							}
						},
						secondary: {
							label: __("Discard")
						}
					}
				})
				dialog.set_values(doc)

				const $element = $(dialog.body)
				$element.append(`
					<div class="qe-fp" style="padding-top: '15px'; padding-bottom: '15px'; padding-left: '7px'">
						<button class="btn btn-default btn-sm">
							${__("Edit in Full Page")}
						</button>
					</div>
				`)
				$element.find('.qe-fp').click(() => {
					dialog.hide()
					dataent.set_route(`Form/${doctype}/${docname}`)
				})

				dialog.show()
			})
		})
	})
}

// dataent._
// dataent's utility namespace.
dataent.provide('dataent._')

// String Utilities

/**
 * @description Python-inspired format extension for string objects.
 *
 * @param  {string} string - A string with placeholders.
 * @param  {object} object - An object with placeholder, value pairs.
 *
 * @return {string}        - The formatted string.
 *
 * @example
 * dataent._.format('{foo} {bar}', { bar: 'foo', foo: 'bar' })
 * // returns "bar foo"
 */
dataent._.format = (string, object) => {
	for (const key in object)
		string  = string.replace(`{${key}}`, object[key])

	return string
}

/**
 * @description Fuzzy Search a given query within a dataset.
 *
 * @param  {string} query   - A query string.
 * @param  {array}  dataset - A dataset to search within, can contain singletons or objects.
 * @param  {object} options - Options as per fuze.js
 *
 * @return {array}          - The fuzzy matched index/object within the dataset.
 *
 * @example
 * dataent._.fuzzy_search("foobar", ["foobar", "bartender"])
 * // returns [0, 1]
 *
 * @see http://fusejs.io
 */
dataent._.fuzzy_search = (query, dataset, options) => {
	const DEFAULT     = {
				shouldSort: true,
				 threshold: 0.6,
				  location: 0,
				  distance: 100,
		minMatchCharLength: 1,
		  maxPatternLength: 32
	}
	options       = { ...DEFAULT, ...options }

	const fuse    = new Fuse(dataset, options)
	const result  = fuse.search(query)

	return result
}

/**
 * @description Pluralizes a given word.
 *
 * @param  {string} word  - The word to be pluralized.
 * @param  {number} count - The count.
 *
 * @return {string}       - The pluralized string.
 *
 * @example
 * dataent._.pluralize('member',  1)
 * // returns "member"
 * dataent._.pluralize('members', 0)
 * // returns "members"
 *
 * @todo Handle more edge cases.
 */
dataent._.pluralize = (word, count = 0, suffix = 's') => `${word}${count === 1 ? '' : suffix}`

/**
 * @description Captializes a given string.
 *
 * @param   {word}  - The word to be capitalized.
 *
 * @return {string} - The capitalized word.
 *
 * @example
 * dataent._.capitalize('foobar')
 * // returns "Foobar"
 */
dataent._.capitalize = word => `${word.charAt(0).toUpperCase()}${word.slice(1)}`

// Array Utilities

/**
 * @description Returns the first element of an array.
 *
 * @param   {array} array - The array.
 *
 * @returns - The first element of an array, undefined elsewise.
 *
 * @example
 * dataent._.head([1, 2, 3])
 * // returns 1
 * dataent._.head([])
 * // returns undefined
 */
dataent._.head = arr => dataent._.is_empty(arr) ? undefined : arr[0]

/**
 * @description Returns a copy of the given array (shallow).
 *
 * @param   {array} array - The array to be copied.
 *
 * @returns {array}       - The copied array.
 *
 * @example
 * dataent._.copy_array(["foobar", "barfoo"])
 * // returns ["foobar", "barfoo"]
 *
 * @todo Add optional deep copy.
 */
dataent._.copy_array = array => {
	if ( Array.isArray(array) )
		return array.slice()
	else
		throw dataent.TypeError(`Expected Array, recieved ${typeof array} instead.`)
}

/**
 * @description Check whether an array|string|object|jQuery is empty.
 *
 * @param   {any}     value - The value to be checked on.
 *
 * @returns {boolean}       - Returns if the object is empty.
 *
 * @example
 * dataent._.is_empty([])      // returns true
 * dataent._.is_empty(["foo"]) // returns false
 *
 * dataent._.is_empty("")      // returns true
 * dataent._.is_empty("foo")   // returns false
 *
 * dataent._.is_empty({ })            // returns true
 * dataent._.is_empty({ foo: "bar" }) // returns false
 *
 * dataent._.is_empty($('.papito'))   // returns false
 *
 * @todo Handle other cases.
 */
dataent._.is_empty = value => {
	let empty = false

	if ( value === undefined || value === null )
		empty = true
	else
	if ( Array.isArray(value) || typeof value === 'string' || value instanceof $ )
		empty = value.length === 0
	else
	if ( typeof value === 'object' )
		empty = Object.keys(value).length === 0

	return empty
}

/**
 * @description Converts a singleton to an array, if required.
 *
 * @param {object} item - An object
 *
 * @example
 * dataent._.as_array("foo")
 * // returns ["foo"]
 *
 * dataent._.as_array(["foo"])
 * // returns ["foo"]
 *
 * @see https://docs.oracle.com/javase/8/docs/api/java/util/Arrays.html#asList-T...-
 */
dataent._.as_array = item => Array.isArray(item) ? item : [item]

/**
 * @description Return a singleton if array contains a single element.
 *
 * @param   {array}        list - An array to squash.
 *
 * @returns {array|object}      - Returns an array if there's more than 1 object else the first object itself.
 *
 * @example
 * dataent._.squash(["foo"])
 * // returns "foo"
 *
 * dataent._.squash(["foo", "bar"])
 * // returns ["foo", "bar"]
 */
dataent._.squash = list => Array.isArray(list) && list.length === 1 ? list[0] : list

/**
 * @description Returns true, if the current device is a mobile device.
 *
 * @example
 * dataent._.is_mobile()
 * // returns true|false
 *
 * @see https://developer.mozilla.org/en-US/docs/Web/HTTP/Browser_detection_using_the_user_agent
 */
dataent._.is_mobile = () => {
	const regex    = new RegExp("Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini", "i")
	const agent    = navigator.userAgent
	const mobile   = regex.test(agent)

	return mobile
}

/**
 * @description Removes falsey values from an array.
 *
 * @example
 * dataent._.compact([1, 2, false, NaN, ''])
 * // returns [1, 2]
 */
dataent._.compact   = array => array.filter(Boolean)

// extend utils to base.
dataent.utils       = { ...dataent.utils, ...dataent._ }

// dataent extensions

// dataent.user extensions
/**
 * @description Returns the first name of a User.
 *
 * @param {string} user - User
 *
 * @returns The first name of the user.
 *
 * @example
 * dataent.user.first_name("Rahul Malhotra")
 * // returns "Rahul"
 */
dataent.provide('dataent.user')
dataent.user.first_name = user => dataent._.head(dataent.user.full_name(user).split(" "))

dataent.provide('dataent.ui.keycode')
dataent.ui.keycode = { RETURN: 13 }

/**
 * @description Dataent's Store Class
 */
 // dataent.stores  - A registry for dataent stores.
dataent.provide('dataent.stores')
dataent.stores = [ ]
dataent.Store  = class
{
	/**
	 * @description Dataent's Store Class's constructor.
	 *
	 * @param {string} name - Name of the logger.
	 */
	constructor (name) {
		if ( typeof name !== 'string' )
			throw new dataent.TypeError(`Expected string for name, got ${typeof name} instead.`)
		this.name = name
	}

	/**
	 * @description Get instance of dataent.Store (return registered one if declared).
	 *
	 * @param {string} name - Name of the store.
	 */
	static get (name) {
		if ( !(name in dataent.stores) )
			dataent.stores[name] = new dataent.Store(name)
		return dataent.stores[name]
	}

	set (key, value) { localStorage.setItem(`${this.name}:${key}`, value) }
	get (key, value) { return localStorage.getItem(`${this.name}:${key}`) }
}

// dataent.loggers - A registry for dataent loggers.
dataent.provide('dataent.loggers')
/**
 * @description Dataent's Logger Class
 *
 * @example
 * dataent.log       = dataent.Logger.get('foobar')
 * dataent.log.level = dataent.Logger.DEBUG
 *
 * dataent.log.info('foobar')
 * // prints '[timestamp] foobar: foobar'
 */
dataent.Logger = class {
	/**
	 * @description Dataent's Logger Class's constructor.
	 *
	 * @param {string} name - Name of the logger.
	 */
	constructor (name, level) {
		if ( typeof name !== 'string' )
			throw new dataent.TypeError(`Expected string for name, got ${typeof name} instead.`)

		this.name   = name
		this.level  = level

		if ( !this.level ) {
			if ( dataent.boot.developer_mode )
				this.level = dataent.Logger.ERROR
			else
				this.level = dataent.Logger.NOTSET
		}
		this.format = dataent.Logger.FORMAT
	}

	/**
	 * @description Get instance of dataent.Logger (return registered one if declared).
	 *
	 * @param {string} name - Name of the logger.
	 */
	static get (name, level) {
		if ( !(name in dataent.loggers) )
			dataent.loggers[name] = new dataent.Logger(name, level)
		return dataent.loggers[name]
	}

	debug (message) { this.log(message, dataent.Logger.DEBUG) }
	info  (message) { this.log(message, dataent.Logger.INFO)  }
	warn  (message) { this.log(message, dataent.Logger.WARN)  }
	error (message) { this.log(message, dataent.Logger.ERROR) }

	log (message, level) {
		const timestamp   = dataent.datetime.now()

		if ( level.value <= this.level.value ) {
			const format  = dataent._.format(this.format, {
				time: timestamp.format('HH:mm:ss'),
				name: this.name
			})
			console.log(`%c ${format}:`, `color: ${level.color}`, message)
		}
	}
}

dataent.Logger.DEBUG  = { value: 10, color: '#616161', name: 'DEBUG'  }
dataent.Logger.INFO   = { value: 20, color: '#2196F3', name: 'INFO'   }
dataent.Logger.WARN   = { value: 30, color: '#FFC107', name: 'WARN'   }
dataent.Logger.ERROR  = { value: 40, color: '#F44336', name: 'ERROR'  }
dataent.Logger.NOTSET = { value:  0,                   name: 'NOTSET' }

dataent.Logger.FORMAT = '{time} {name}'

// dataent.chat
dataent.provide('dataent.chat')

dataent.log = dataent.Logger.get('dataent.chat', dataent.Logger.NOTSET)

// dataent.chat.profile
dataent.provide('dataent.chat.profile')

/**
 * @description Create a Chat Profile.
 *
 * @param   {string|array} fields - (Optional) fields to be retrieved after creating a Chat Profile.
 * @param   {function}     fn     - (Optional) callback with the returned Chat Profile.
 *
 * @returns {Promise}
 *
 * @example
 * dataent.chat.profile.create(console.log)
 *
 * dataent.chat.profile.create("status").then(console.log) // { status: "Online" }
 */
dataent.chat.profile.create = (fields, fn) => {
	if ( typeof fields === "function" ) {
		fn     = fields
		fields = null
	} else
	if ( typeof fields === "string" )
		fields = dataent._.as_array(fields)

	return new Promise(resolve => {
		dataent.call("dataent.chat.doctype.chat_profile.chat_profile.create",
			{ user: dataent.session.user, exists_ok: true, fields: fields },
				response => {
					if ( fn )
						fn(response.message)

					resolve(response.message)
				})
	})
}

/**
 * @description Updates a Chat Profile.
 *
 * @param   {string} user   - (Optional) Chat Profile User, defaults to session user.
 * @param   {object} update - (Required) Updates to be dispatched.
 *
 * @example
 * dataent.chat.profile.update(dataent.session.user, { "status": "Offline" })
 */
dataent.chat.profile.update = (user, update, fn) => {
	return new Promise(resolve => {
		dataent.call("dataent.chat.doctype.chat_profile.chat_profile.update",
			{ user: user || dataent.session.user, data: update },
				response => {
					if ( fn )
						fn(response.message)

					resolve(response.message)
				})
	})
}

// dataent.chat.profile.on
dataent.provide('dataent.chat.profile.on')

/**
 * @description Triggers on a Chat Profile update of a user (Only if there's a one-on-one conversation).
 *
 * @param   {function} fn - (Optional) callback with the User and the Chat Profile update.
 *
 * @returns {Promise}
 *
 * @example
 * dataent.chat.profile.on.update(function (user, update)
 * {
 *      // do stuff
 * })
 */
dataent.chat.profile.on.update = function (fn) {
	dataent.realtime.on("dataent.chat.profile:update", r => fn(r.user, r.data))
}
dataent.chat.profile.STATUSES
=
[
	{
		name: "Online",
	   color: "green"
	},
	{
		 name: "Away",
		color: "yellow"
	},
	{
		 name: "Busy",
		color: "red"
	},
	{
		 name: "Offline",
		color: "darkgrey"
	}
]

// dataent.chat.room
dataent.provide('dataent.chat.room')

/**
 * @description Creates a Chat Room.
 *
 * @param   {string}       kind  - (Required) "Direct", "Group" or "Visitor".
 * @param   {string}       owner - (Optional) Chat Room owner (defaults to current user).
 * @param   {string|array} users - (Required for "Direct" and "Visitor", Optional for "Group") User(s) within Chat Room.
 * @param   {string}       name  - Chat Room name.
 * @param   {function}     fn    - callback with created Chat Room.
 *
 * @returns {Promise}
 *
 * @example
 * dataent.chat.room.create("Direct", dataent.session.user, "foo@bar.com", function (room) {
 *      // do stuff
 * })
 * dataent.chat.room.create("Group",  dataent.session.user, ["santa@gmail.com", "banta@gmail.com"], "Santa and Banta", function (room) {
 *      // do stuff
 * })
 */
dataent.chat.room.create = function (kind, owner, users, name, fn) {
	if ( typeof name === "function" ) {
		fn   = name
		name = null
	}

	users    = dataent._.as_array(users)

	return new Promise(resolve => {
		dataent.call("dataent.chat.doctype.chat_room.chat_room.create",
			{ kind: kind, owner: owner || dataent.session.user, users: users, name: name },
			r => {
				let room = r.message
				room     = { ...room, creation: new dataent.datetime.datetime(room.creation) }

				if ( fn )
					fn(room)

				resolve(room)
			})
	})
}

/**
 * @description Returns Chat Room(s).
 *
 * @param   {string|array} names   - (Optional) Chat Room(s) to retrieve.
 * @param   {string|array} fields  - (Optional) fields to be retrieved for each Chat Room.
 * @param   {function}     fn      - (Optional) callback with the returned Chat Room(s).
 *
 * @returns {Promise}
 *
 * @example
 * dataent.chat.room.get(function (rooms) {
 *      // do stuff
 * })
 * dataent.chat.room.get().then(function (rooms) {
 *      // do stuff
 * })
 *
 * dataent.chat.room.get(null, ["room_name", "avatar"], function (rooms) {
 *      // do stuff
 * })
 *
 * dataent.chat.room.get("CR00001", "room_name", function (room) {
 *      // do stuff
 * })
 *
 * dataent.chat.room.get(["CR00001", "CR00002"], ["room_name", "last_message"], function (rooms) {
 *
 * })
 */
dataent.chat.room.get = function (names, fields, fn) {
	if ( typeof names === "function" ) {
		fn     = names
		names  = null
		fields = null
	}
	else
	if ( typeof names === "string" ) {
		names  = dataent._.as_array(names)

		if ( typeof fields === "function" ) {
			fn     = fields
			fields = null
		}
		else
		if ( typeof fields === "string" )
			fields = dataent._.as_array(fields)
	}

	return new Promise(resolve => {
		dataent.call("dataent.chat.doctype.chat_room.chat_room.get",
			{ user: dataent.session.user, rooms: names, fields: fields },
				response => {
					let rooms = response.message
					if ( rooms ) { // dataent.api BOGZ! (emtpy arrays are falsified, not good design).
						rooms = dataent._.as_array(rooms)
						rooms = rooms.map(room => {
							return { ...room, creation: new dataent.datetime.datetime(room.creation),
								last_message: room.last_message ? {
									...room.last_message,
									creation: new dataent.datetime.datetime(room.last_message.creation)
								} : null
							}
						})
						rooms = dataent._.squash(rooms)
					}
					else
						rooms = [ ]

					if ( fn )
						fn(rooms)

					resolve(rooms)
				})
	})
}

/**
 * @description Subscribe current user to said Chat Room(s).
 *
 * @param {string|array} rooms - Chat Room(s).
 *
 * @example
 * dataent.chat.room.subscribe("CR00001")
 */
dataent.chat.room.subscribe = function (rooms) {
	dataent.realtime.publish("dataent.chat.room:subscribe", rooms)
}

/**
 * @description Get Chat Room history.
 *
 * @param   {string} name - Chat Room name
 *
 * @returns {Promise}     - Chat Message(s)
 *
 * @example
 * dataent.chat.room.history(function (messages)
 * {
 *      // do stuff.
 * })
 */
dataent.chat.room.history = function (name, fn) {
	return new Promise(resolve => {
		dataent.call("dataent.chat.doctype.chat_room.chat_room.history",
			{ room: name, user: dataent.session.user },
				r => {
					let messages = r.message ? dataent._.as_array(r.message) : [ ] // dataent.api BOGZ! (emtpy arrays are falsified, not good design).
					messages     = messages.map(m => {
						return { ...m,
							creation: new dataent.datetime.datetime(m.creation)
						}
					})

					if ( fn )
						fn(messages)

					resolve(messages)
				})
	})
}

/**
 * @description Searches Rooms based on a query.
 *
 * @param   {string} query - The query string.
 * @param   {array}  rooms - A list of Chat Rooms.
 *
 * @returns {array}        - A fuzzy searched list of rooms.
 */
dataent.chat.room.search = function (query, rooms) {
	const dataset = rooms.map(r => {
		if ( r.room_name )
			return r.room_name
		else
			if ( r.owner === dataent.session.user )
				return dataent.user.full_name(dataent._.squash(r.users))
			else
				return dataent.user.full_name(r.owner)
	})
	const results = dataent._.fuzzy_search(query, dataset)
	rooms         = results.map(i => rooms[i])

	return rooms
}

/**
 * @description Sort Chat Room(s) based on Last Message Timestamp or Creation Date.
 *
 * @param {array}   - A list of Chat Room(s)
 * @param {compare} - (Optional) a comparision function.
 */
dataent.chat.room.sort = function (rooms, compare = null) {
	compare = compare || function (a, b) {
		if ( a.last_message && b.last_message )
			return dataent.datetime.compare(a.last_message.creation, b.last_message.creation)
		else
		if ( a.last_message )
			return dataent.datetime.compare(a.last_message.creation, b.creation)
		else
		if ( b.last_message )
			return dataent.datetime.compare(a.creation, b.last_message.creation)
		else
			return dataent.datetime.compare(a.creation, b.creation)
	}
	rooms.sort(compare)

	return rooms
}

// dataent.chat.room.on
dataent.provide('dataent.chat.room.on')

/**
 * @description Triggers on Chat Room updated.
 *
 * @param {function} fn - callback with the Chat Room and Update.
 */
dataent.chat.room.on.update = function (fn) {
	dataent.realtime.on("dataent.chat.room:update", r => {
		if ( r.data.last_message )
			// creation to dataent.datetime.datetime (easier to manipulate).
			r.data = { ...r.data, last_message: { ...r.data.last_message, creation: new dataent.datetime.datetime(r.data.last_message.creation) } }

		fn(r.room, r.data)
	})
}

/**
 * @description Triggers on Chat Room created.
 *
 * @param {function} fn - callback with the created Chat Room.
 */
dataent.chat.room.on.create = function (fn) {
	dataent.realtime.on("dataent.chat.room:create", r =>
		fn({ ...r, creation: new dataent.datetime.datetime(r.creation) })
	)
}

/**
 * @description Triggers when a User is typing in a Chat Room.
 *
 * @param {function} fn - callback with the typing User within the Chat Room.
 */
dataent.chat.room.on.typing = function (fn) {
	dataent.realtime.on("dataent.chat.room:typing", r => fn(r.room, r.user))
}

// dataent.chat.message
dataent.provide('dataent.chat.message')

dataent.chat.message.typing = function (room, user) {
	dataent.realtime.publish("dataent.chat.message:typing", { user: user || dataent.session.user, room: room })
}

dataent.chat.message.send   = function (room, message, type = "Content") {
	dataent.call("dataent.chat.doctype.chat_message.chat_message.send",
		{ user: dataent.session.user, room: room, content: message, type: type })
}

dataent.chat.message.update = function (message, update, fn) {
	return new Promise(resolve => {
		dataent.call('dataent.chat.doctype.chat_message.chat_message.update',
			{ user: dataent.session.user, message: message, update: update },
			r =>  {
				if ( fn )
					fn(response.message)

				resolve(response.message)
			})
	})
}

dataent.chat.message.sort   = (messages) => {
	if ( !dataent._.is_empty(messages) )
		messages.sort((a, b) => dataent.datetime.compare(b.creation, a.creation))

	return messages
}

/**
 * @description Add user to seen (defaults to session.user)
 */
dataent.chat.message.seen   = (mess, user) => {
	dataent.call('dataent.chat.doctype.chat_message.chat_message.seen',
		{ message: mess, user: user || dataent.session.user })
}

dataent.provide('dataent.chat.message.on')
dataent.chat.message.on.create = function (fn) {
	dataent.realtime.on("dataent.chat.message:create", r =>
		fn({ ...r, creation: new dataent.datetime.datetime(r.creation) })
	)
}

dataent.chat.message.on.update = function (fn) {
	dataent.realtime.on("dataent.chat.message:update", r => fn(r.message, r.data))
}

dataent.chat.pretty_datetime   = function (date) {
	const today    = moment()
	const instance = date.moment

	if ( today.isSame(instance, "d") )
		return instance.format("hh:mm A")
	else
	if ( today.isSame(instance, "week") )
		return instance.format("dddd")
	else
		return instance.format("DD/MM/YYYY")
}

// dataent.chat.sound
dataent.provide('dataent.chat.sound')

/**
 * @description Plays a given registered sound.
 *
 * @param {value} - The name of the registered sound.
 *
 * @example
 * dataent.chat.sound.play("message")
 */
dataent.chat.sound.play  = function (name, volume = 0.1) {
	// dataent._.play_sound(`chat-${name}`)
	const $audio = $(`<audio class="chat-audio"/>`)
	$audio.attr('volume', volume)

	if  ( dataent._.is_empty($audio) )
		$(document).append($audio)

	if  ( !$audio.paused ) {
		dataent.log.info('Stopping sound playing.')
		$audio[0].pause()
		$audio.attr('currentTime', 0)
	}

	dataent.log.info('Playing sound.')
	$audio.attr('src', `${dataent.chat.sound.PATH}/chat-${name}.mp3`)
	$audio[0].play()
}
dataent.chat.sound.PATH  = '/assets/dataent/sounds'

// dataent.chat.emoji
dataent.chat.emojis = [ ]
dataent.chat.emoji  = function (fn) {
	return new Promise(resolve => {
		if ( !dataent._.is_empty(dataent.chat.emojis) ) {
			if ( fn )
				fn(dataent.chat.emojis)

			resolve(dataent.chat.emojis)
		}
		else
			$.get('https://cdn.rawgit.com/dataent/emoji/master/emoji', (data) => {
				dataent.chat.emojis = JSON.parse(data)

				if ( fn )
					fn(dataent.chat.emojis)

				resolve(dataent.chat.emojis)
			})
	})
}

// Website Settings
dataent.provide('dataent.chat.website.settings')
dataent.chat.website.settings = (fields, fn) =>
{
	if ( typeof fields === "function" ) {
		fn     = fields
		fields = null
	} else
	if ( typeof fields === "string" )
		fields = dataent._.as_array(fields)

	return new Promise(resolve => {
		dataent.call("dataent.chat.website.settings",
			{ fields: fields })
			.then(response => {
				var message = response.message

				if ( message.enable_from )
					message   = { ...message, enable_from: new dataent.datetime.datetime(message.enable_from, 'HH:mm:ss') }
				if ( message.enable_to )
					message   = { ...message, enable_to:   new dataent.datetime.datetime(message.enable_to,   'HH:mm:ss') }

				if ( fn )
					fn(message)

				resolve(message)
			})
	})
}

dataent.chat.website.token    = (fn) =>
{
	return new Promise(resolve => {
		dataent.call("dataent.chat.website.token")
			.then(response => {
				if ( fn )
					fn(response.message)

				resolve(response.message)
			})
	})
}

const { h, Component } = hyper

// dataent.components
// dataent's component namespace.
dataent.provide('dataent.components')

dataent.provide('dataent.chat.component')

/**
 * @description Button Component
 *
 * @prop {string}  type  - (Optional) "default", "primary", "info", "success", "warning", "danger" (defaults to "default")
 * @prop {boolean} block - (Optional) Render a button block (defaults to false).
 */
dataent.components.Button
=
class extends Component {
	render ( ) {
		const { props } = this
		const size      = dataent.components.Button.SIZE[props.size]

		return (
			h("button", { ...props, class: `btn ${size && size.class} btn-${props.type} ${props.block ? "btn-block" : ""} ${props.class ? props.class : ""}` },
				props.children
			)
		)
	}
}
dataent.components.Button.SIZE
=
{
	small: {
		class: "btn-sm"
	},
	large: {
		class: "btn-lg"
	}
}
dataent.components.Button.defaultProps
=
{
	 type: "default",
	block: false
}

/**
 * @description FAB Component
 *
 * @extends dataent.components.Button
 */
dataent.components.FAB
=
class extends dataent.components.Button {
	render ( ) {
		const { props } = this
		const size      = dataent.components.FAB.SIZE[props.size]

		return (
			h(dataent.components.Button, { ...props, class: `${props.class} ${size && size.class}`},
				h("i", { class: props.icon })
			)
		)
	}
}
dataent.components.FAB.defaultProps
=
{
	icon: "octicon octicon-plus"
}
dataent.components.FAB.SIZE
=
{
	small:
	{
		class: "dataent-fab-sm"
	},
	large:
	{
		class: "dataent-fab-lg"
	}
}

/**
 * @description Octicon Component
 *
 * @prop color - (Required) color for the indicator
 */
dataent.components.Indicator
=
class extends Component {
	render ( ) {
		const { props } = this

		return props.color ? h("span", { ...props, class: `indicator ${props.color}` }) : null
	}
}

/**
 * @description FontAwesome Component
 */
dataent.components.FontAwesome
=
class extends Component {
	render ( ) {
		const { props } = this

		return props.type ? h("i", { ...props, class: `fa ${props.fixed ? "fa-fw" : ""} fa-${props.type} ${props.class}` }) : null
	}
}
dataent.components.FontAwesome.defaultProps
=
{
	fixed: false
}

/**
 * @description Octicon Component
 *
 * @extends dataent.Component
 */
dataent.components.Octicon
=
class extends Component {
	render ( ) {
		const { props } = this

		return props.type ? h("i", { ...props, class: `octicon octicon-${props.type}` }) : null
	}
}

/**
 * @description Avatar Component
 *
 * @prop {string} title - (Optional) title for the avatar.
 * @prop {string} abbr  - (Optional) abbreviation for the avatar, defaults to the first letter of the title.
 * @prop {string} size  - (Optional) size of the avatar to be displayed.
 * @prop {image}  image - (Optional) image for the avatar, defaults to the first letter of the title.
 */
dataent.components.Avatar
=
class extends Component {
	render ( ) {
		const { props } = this
		const abbr      = props.abbr || props.title.substr(0, 1)
		const size      = dataent.components.Avatar.SIZE[props.size] || dataent.components.Avatar.SIZE.medium

		return (
			h("span", { class: `avatar ${size.class} ${props.class ? props.class : ""}` },
				props.image ?
					h("img", { class: "media-object", src: props.image })
					:
					h("div", { class: "standard-image" }, abbr)
			)
		)
	}
}
dataent.components.Avatar.SIZE
=
{
	small:
	{
		class: "avatar-small"
	},
	large:
	{
		class: "avatar-large"
	},
	medium:
	{
		class: "avatar-medium"
	}
}

/**
 * @description Dataent Chat Object.
 *
 * @example
 * const chat = new dataent.Chat(options) // appends to "body"
 * chat.render()
 * const chat = new dataent.Chat(".selector", options)
 * chat.render()
 *
 * const chat = new dataent.Chat()
 * chat.set_wrapper('.selector')
 *     .set_options(options)
 *     .render()
 */
dataent.Chat
=
class {
	/**
	 * @description Dataent Chat Object.
	 *
	 * @param {string} selector - A query selector, HTML Element or jQuery object.
	 * @param {object} options  - Optional configurations.
	 */
	constructor (selector, options) {
		if ( !(typeof selector === "string" || selector instanceof $ || selector instanceof HTMLElement) ) {
			options  = selector
			selector = null
		}

		this.options = dataent.Chat.OPTIONS

		this.set_wrapper(selector ? selector : "body")
		this.set_options(options)

		// Load Emojis.
		dataent.chat.emoji()
	}

	/**
	 * Set the container on which the chat widget is mounted on.
	 * @param   {string|HTMLElement} selector - A query selector, HTML Element or jQuery object.
	 *
	 * @returns {dataent.Chat}                 - The instance.
	 *
	 * @example
	 * const chat = new dataent.Chat()
	 * chat.set_wrapper(".selector")
	 */
	set_wrapper (selector) {
		this.$wrapper = $(selector)

		return this
	}

	/**
	 * Set the configurations for the chat interface.
	 * @param   {object}      options - Optional Configurations.
	 *
	 * @returns {dataent.Chat}         - The instance.
	 *
	 * @example
	 * const chat = new dataent.Chat()
	 * chat.set_options({ layout: dataent.Chat.Layout.PAGE })
	 */
	set_options (options) {
		this.options = { ...this.options, ...options }

		return this
	}

	/**
	 * @description Destory the chat widget.
	 *
	 * @returns {dataent.Chat} - The instance.
	 *
	 * @example
	 * const chat = new dataent.Chat()
	 * chat.render()
	 *     .destroy()
	 */
	destroy ( ) {
		const $wrapper = this.$wrapper
		$wrapper.remove(".dataent-chat")

		return this
	}

	/**
	 * @description Render the chat widget component onto destined wrapper.
	 *
	 * @returns {dataent.Chat} - The instance.
	 *
	 * @example
	 * const chat = new dataent.Chat()
	 * chat.render()
	 */
	render (props = { }) {
		this.destroy()

		const $wrapper   = this.$wrapper
		const options    = this.options

		const component  = h(dataent.Chat.Widget, {
			layout: options.layout,
			target: options.target,
			...props
		})

		hyper.render(component, $wrapper[0])

		return this
	}
}
dataent.Chat.Layout
=
{
	PAGE: "page", POPPER: "popper"
}
dataent.Chat.OPTIONS
=
{
	layout: dataent.Chat.Layout.POPPER
}

/**
 * @description The base Component for Dataent Chat
 */
dataent.Chat.Widget
=
class extends Component {
	constructor (props) {
		super (props)

		this.setup(props)
		this.make()
	}

	setup (props) {
		// room actions
		this.room           = { }
		this.room.add       = rooms => {
			rooms           = dataent._.as_array(rooms)
			const names     = rooms.map(r => r.name)

			dataent.log.info(`Subscribing ${dataent.session.user} to Chat Rooms ${names.join(", ")}.`)
			dataent.chat.room.subscribe(names)

			const state     = [ ]

			for (const room of rooms)
				if ( ["Group", "Visitor"].includes(room.type) || room.owner === dataent.session.user || room.last_message ) {
					dataent.log.info(`Adding ${room.name} to component.`)
					state.push(room)
				}

			this.set_state({ rooms: [ ...this.state.rooms, ...state ] })
		}
		this.room.update    = (room, update) => {
			const { state } = this
			var   exists    = false
			const rooms     = state.rooms.map(r => {
				if ( r.name === room ) {
					exists  = true
					if ( update.typing ) {
						if ( !dataent._.is_empty(r.typing) ) {
							const usr = update.typing
							if ( !r.typing.includes(usr) ) {
								update.typing = dataent._.copy_array(r.typing)
								update.typing.push(usr)
							}
						}
						else
							update.typing = dataent._.as_array(update.typing)
					}

					return { ...r, ...update }
				}

				return r
			})

			if ( dataent.session.user !== 'Guest' ) {
				if ( !exists )
					dataent.chat.room.get(room, (room) => this.room.add(room))
				else
					this.set_state({ rooms })
			}

			if ( state.room.name === room ) {
				if ( update.typing ) {
					if ( !dataent._.is_empty(state.room.typing) ) {
						const usr = update.typing
						if ( !state.room.typing.includes(usr) ) {
							update.typing = dataent._.copy_array(state.room.typing)
							update.typing.push(usr)
						}
					} else
						update.typing = dataent._.as_array(update.typing)
				}

				const room  = { ...state.room, ...update }

				this.set_state({ room })
			}
		}
		this.room.select    = (name) => {
			dataent.chat.room.history(name, (messages) => {
				const  { state } = this
				const room       = state.rooms.find(r => r.name === name)

				this.set_state({
					room: { ...state.room, ...room, messages: messages }
				})
			})
		}

		this.state = { ...dataent.Chat.Widget.defaultState, ...props }
	}

	make ( ) {
		if ( dataent.session.user !== 'Guest' ) {
			dataent.chat.profile.create([
				"status", "message_preview", "notification_tones", "conversation_tones"
			]).then(profile => {
				this.set_state({ profile })

				dataent.chat.room.get(rooms => {
					rooms = dataent._.as_array(rooms)
					dataent.log.info(`User ${dataent.session.user} is subscribed to ${rooms.length} ${dataent._.pluralize('room', rooms.length)}.`)

					if ( !dataent._.is_empty(rooms) )
						this.room.add(rooms)
				})

				this.bind()
			})
		} else {
			this.bind()
		}
	}

	bind ( ) {
		dataent.chat.profile.on.update((user, update) => {
			dataent.log.warn(`TRIGGER: Chat Profile update ${JSON.stringify(update)} of User ${user}.`)

			if ( 'status' in update ) {
				if ( user === dataent.session.user ) {
					this.set_state({
						profile: { ...this.state.profile, status: update.status }
					})
				} else {
					const status = dataent.chat.profile.STATUSES.find(s => s.name === update.status)
					const color  = status.color

					const alert  = `<span class="indicator ${color}"/> ${dataent.user.full_name(user)} is currently <b>${update.status}</b>`
					dataent.show_alert(alert, 3)
				}
			}
		})

		dataent.chat.room.on.create((room) => {
			dataent.log.warn(`TRIGGER: Chat Room ${room.name} created.`)
			this.room.add(room)
		})

		dataent.chat.room.on.update((room, update) => {
			dataent.log.warn(`TRIGGER: Chat Room ${room} update ${JSON.stringify(update)} recieved.`)
			this.room.update(room, update)
		})

		dataent.chat.room.on.typing((room, user) => {
			if ( user !== dataent.session.user ) {
				dataent.log.warn(`User ${user} typing in Chat Room ${room}.`)
				this.room.update(room, { typing: user })

				setTimeout(() => this.room.update(room, { typing: null }), 5000)
			}
		})

		dataent.chat.message.on.create((r) => {
			const { state } = this

			// play sound.
			if ( state.room.name )
				state.profile.conversation_tones && dataent.chat.sound.play('message')
			else
				state.profile.notification_tones && dataent.chat.sound.play('notification')

			if ( r.user !== dataent.session.user && state.profile.message_preview && !state.toggle ) {
				const $element = $('body').find('.dataent-chat-alert')
				$element.remove()

				const  alert   = // TODO: ellipses content
				`
				<span data-action="show-message" class="cursor-pointer">
					<span class="indicator yellow"/> <b>${dataent.user.first_name(r.user)}</b>: ${r.content}
				</span>
				`
				dataent.show_alert(alert, 3, {
					"show-message": function (r) {
						this.room.select(r.room)
						this.base.firstChild._component.toggle()
					}.bind(this, r)
				})
			}

			if ( r.room === state.room.name ) {
				const mess  = dataent._.copy_array(state.room.messages)
				mess.push(r)

				this.set_state({ room: { ...state.room, messages: mess } })
			}
		})

		dataent.chat.message.on.update((message, update) => {
			dataent.log.warn(`TRIGGER: Chat Message ${message} update ${JSON.stringify(update)} recieved.`)
		})
	}

	render ( ) {
		const { props, state } = this
		const me               = this

		const ActionBar        = h(dataent.Chat.Widget.ActionBar, {
			placeholder: __("Search or Create a New Chat"),
				  class: "level",
				 layout: props.layout,
				actions:
			dataent._.compact([
				{
					  label: __("New"),
					onclick: function ( ) {
						const dialog = new dataent.ui.Dialog({
							  title: __("New Chat"),
							 fields: [
								 {
										 label: __("Chat Type"),
									 fieldname: "type",
									 fieldtype: "Select",
									   options: ["Group", "Direct Chat"],
									   default: "Group",
									  onchange: () =>  {
											const type     = dialog.get_value("type")
											const is_group = type === "Group"

											dialog.set_df_property("group_name", "reqd",  is_group)
											dialog.set_df_property("user",       "reqd", !is_group)
									  }
								 },
								 {
										 label: __("Group Name"),
									 fieldname: "group_name",
									 fieldtype: "Data",
										  reqd: true,
									depends_on: "eval:doc.type == 'Group'"
								 },
								 {
										 label: __("Users"),
									 fieldname: "users",
									 fieldtype: "MultiSelect",
									   options: dataent.user.get_emails(),
									depends_on: "eval:doc.type == 'Group'"
								 },
								 {
										 label: __("User"),
									 fieldname: "user",
									 fieldtype: "Link",
									   options: "User",
									depends_on: "eval:doc.type == 'Direct Chat'"
								 }
							 ],
							action: {
								primary: {
									   label: __("Create"),
									onsubmit: (values) => {
										if ( values.type === "Group" ) {
											if ( !dataent._.is_empty(values.users) ) {
												const name  = values.group_name
												const users = dialog.fields_dict.users.get_values()

												dataent.chat.room.create("Group",  null, users, name)
											}
										} else {
											const user      = values.user

											dataent.chat.room.create("Direct", null, user)
										}
										dialog.hide()
									}
								}
							}
						})
						dialog.show()
					}
				},
				dataent._.is_mobile() && {
					   icon: "octicon octicon-x",
					   class: "dataent-chat-close",
					onclick: () => this.set_state({ toggle: false })
				}
			], Boolean),
			change: query => { me.set_state({ query }) },
			  span: span  => { me.set_state({ span  }) },
		})

		var   contacts   = [ ]
		if ( 'user_info' in dataent.boot ) {
			const emails = dataent.user.get_emails()
			for (const email of emails) {
				var exists = false

				for (const room of state.rooms) {
					if ( room.type === 'Direct' ) {
						if ( room.owner === email || dataent._.squash(room.users) === email )
							exists = true
					}
				}

				if ( !exists )
					contacts.push({ owner: dataent.session.user, users: [email] })
			}
		}
		const rooms      = state.query ? dataent.chat.room.search(state.query, state.rooms.concat(contacts)) : dataent.chat.room.sort(state.rooms)

		const layout     = state.span  ? dataent.Chat.Layout.PAGE : dataent.Chat.Layout.POPPER

		const RoomList   = dataent._.is_empty(rooms) && !state.query ?
			h("div", { class: "vcenter" },
				h("div", { class: "text-center text-extra-muted" },
					h("p","",__("You don't have any messages yet."))
				)
			)
			:
			h(dataent.Chat.Widget.RoomList, { rooms: rooms, click: room =>  {
				if ( room.name )
					this.room.select(room.name)
				else
					dataent.chat.room.create("Direct", room.owner, dataent._.squash(room.users), ({ name }) => this.room.select(name))
			}})
		const Room       = h(dataent.Chat.Widget.Room, { ...state.room, layout: layout, destroy: () => {
			this.set_state({
				room: { name: null, messages: [ ] }
			})
		}})

		const component  = layout === dataent.Chat.Layout.POPPER ?
			h(dataent.Chat.Widget.Popper, { heading: ActionBar, page: state.room.name && Room, target: props.target,
				toggle: (t) => this.set_state({ toggle: t }) },
				RoomList
			)
			:
			h("div", { class: "dataent-chat-popper" },
				h("div", { class: "dataent-chat-popper-collapse" },
					h("div", { class: "panel panel-default panel-span", style: { width: "25%" } },
						h("div", { class: "panel-heading" },
							ActionBar
						),
						RoomList
					),
					Room
				)
			)

		return (
			h("div", { class: "dataent-chat" },
				component
			)
		)
	}
}
dataent.Chat.Widget.defaultState =  {
	  query: "",
	profile: { },
	  rooms: [ ],
	   room: { name: null, messages: [ ], typing: [ ] },
	 toggle: false,
	   span: false
}
dataent.Chat.Widget.defaultProps = {
	layout: dataent.Chat.Layout.POPPER
}

/**
 * @description Chat Widget Popper HOC.
 */
dataent.Chat.Widget.Popper
=
class extends Component {
	constructor (props) {
		super (props)

		this.setup(props);
	}

	setup (props) {
		this.toggle = this.toggle.bind(this)

		this.state  = dataent.Chat.Widget.Popper.defaultState

		if ( props.target )
			$(props.target).click(() => this.toggle())
	}

	toggle  (active) {
		let toggle
		if ( arguments.length === 1 )
			toggle = active
		else
			toggle = this.state.active ? false : true

		this.set_state({ active: toggle })

		this.props.toggle(toggle)
	}

	on_mounted ( ) {
		$(document.body).on('click', '.page-container, .dataent-chat-close', ({ currentTarget }) => {
			this.toggle(false)
		})
	}

	render  ( )  {
		const { props, state } = this

		return !state.destroy ?
		(
			h("div", { class: "dataent-chat-popper", style: !props.target ? { "margin-bottom": "80px" } : null },
				!props.target ?
					h(dataent.components.FAB, {
						  class: "dataent-fab",
						   icon: state.active ? "fa fa-fw fa-times" : "font-heavy octicon octicon-comment",
						   size: dataent._.is_mobile() ? null : "large",
						   type: "primary",
						onclick: () => this.toggle(),
					}) : null,
				state.active ?
					h("div", { class: "dataent-chat-popper-collapse" },
						props.page ? props.page : (
							h("div", { class: `panel panel-default ${dataent._.is_mobile() ? "panel-span" : ""}` },
								h("div", { class: "panel-heading" },
									props.heading
								),
								props.children
							)
						)
				) : null
			)
		) : null
	}
}
dataent.Chat.Widget.Popper.defaultState
=
{
	 active: false,
	destroy: false
}

/**
 * @description dataent.Chat.Widget ActionBar Component
 */
dataent.Chat.Widget.ActionBar
=
class extends Component {
	constructor (props) {
		super (props)

		this.change = this.change.bind(this)
		this.submit = this.submit.bind(this)

		this.state  = dataent.Chat.Widget.ActionBar.defaultState
	}

	change (e) {
		const { props, state } = this

		this.set_state({
			[e.target.name]: e.target.value
		})

		props.change(state.query)
	}

	submit (e) {
		const { props, state } = this

		e.preventDefault()

		props.submit(state.query)
	}

	render ( ) {
		const me               = this
		const { props, state } = this
		const { actions }      = props

		return (
			h("div", { class: `dataent-chat-action-bar ${props.class ? props.class : ""}` },
				h("form", { oninput: this.change, onsubmit: this.submit },
					h("input", { autocomplete: "off", class: "form-control input-sm", name: "query", value: state.query, placeholder: props.placeholder || "Search" }),
				),
				!dataent._.is_empty(actions) ?
					actions.map(action => h(dataent.Chat.Widget.ActionBar.Action, { ...action })) : null,
				!dataent._.is_mobile() ?
					h(dataent.Chat.Widget.ActionBar.Action, {
						icon: `octicon octicon-screen-${state.span ? "normal" : "full"}`,
						onclick: () => {
							const span = !state.span
							me.set_state({ span })
							props.span(span)
						}
					})
					:
					null
			)
		)
	}
}
dataent.Chat.Widget.ActionBar.defaultState
=
{
	query: null,
	 span: false
}

/**
 * @description dataent.Chat.Widget ActionBar's Action Component.
 */
dataent.Chat.Widget.ActionBar.Action
=
class extends Component {
	render ( ) {
		const { props } = this

		return (
			h(dataent.components.Button, { size: "small", class: "btn-action", ...props },
				props.icon ? h("i", { class: props.icon }) : null,
				`${props.icon ? " " : ""}${props.label ? props.label : ""}`
			)
		)
	}
}

/**
 * @description dataent.Chat.Widget RoomList Component
 */
dataent.Chat.Widget.RoomList
=
class extends Component {
	render ( ) {
		const { props } = this
		const rooms     = props.rooms

		return !dataent._.is_empty(rooms) ? (
			h("ul", { class: "dataent-chat-room-list nav nav-pills nav-stacked" },
				rooms.map(room => h(dataent.Chat.Widget.RoomList.Item, { ...room, click: props.click }))
			)
		) : null
	}
}

/**
 * @description dataent.Chat.Widget RoomList's Item Component
 */
dataent.Chat.Widget.RoomList.Item
=
class extends Component {
	render ( ) {
		const { props }    = this
		const item         = { }

		if ( props.type === "Group" ) {
			item.title     = props.room_name
			item.image     = props.avatar

			if ( !dataent._.is_empty(props.typing) ) {
				props.typing  = dataent._.as_array(props.typing) // HACK: (BUG) why does typing return a string?
				const names   = props.typing.map(user => dataent.user.first_name(user))
				item.subtitle = `${names.join(", ")} typing...`
			} else
			if ( props.last_message ) {
				const message = props.last_message
				const content = message.content

				if ( message.type === "File" ) {
					item.subtitle = `📁 ${content.name}`
				} else {
					item.subtitle = props.last_message.content
				}
			}
		} else {
			const user     = props.owner === dataent.session.user ? dataent._.squash(props.users) : props.owner

			item.title     = dataent.user.full_name(user)
			item.image     = dataent.user.image(user)
			item.abbr      = dataent.user.abbr(user)

			if ( !dataent._.is_empty(props.typing) )
				item.subtitle = 'typing...'
			else
			if ( props.last_message ) {
				const message = props.last_message
				const content = message.content

				if ( message.type === "File" ) {
					item.subtitle = `📁 ${content.name}`
				} else {
					item.subtitle = props.last_message.content
				}
			}
		}

		let is_unread = false
		if ( props.last_message ) {
			item.timestamp = dataent.chat.pretty_datetime(props.last_message.creation)
			is_unread = !props.last_message.seen.includes(dataent.session.user)
		}

		return (
			h("li", null,
				h("a", { class: props.active ? "active": "", onclick: () => {
					if (props.last_message) {
						dataent.chat.message.seen(props.last_message.name);
					}
					props.click(props)
				} },
					h("div", { class: "row" },
						h("div", { class: "col-xs-9" },
							h(dataent.Chat.Widget.MediaProfile, { ...item })
						),
						h("div", { class: "col-xs-3 text-right" },
							[
								h("div", { class: "text-muted", style: { "font-size": "9px" } }, item.timestamp),
								is_unread ? h("span", { class: "indicator red" }) : null
							]
						),
					)
				)
			)
		)
	}
}

/**
 * @description dataent.Chat.Widget's MediProfile Component.
 */
dataent.Chat.Widget.MediaProfile
=
class extends Component {
	render ( ) {
		const { props } = this
		const position  = dataent.Chat.Widget.MediaProfile.POSITION[props.position || "left"]
		const avatar    = (
			h("div", { class: `${position.class} media-middle` },
				h(dataent.components.Avatar, { ...props,
					title: props.title,
					image: props.image,
					 size: props.size,
					 abbr: props.abbr
				})
			)
		)

		return (
			h("div", { class: "media", style: position.class === "media-right" ? { "text-align": "right" } : null },
				position.class === "media-left"  ? avatar : null,
				h("div", { class: "media-body" },
					h("div", { class: "media-heading ellipsis small", style: `max-width: ${props.width_title || "100%"} display: inline-block` }, props.title),
					props.content  ? h("div","",h("small","",props.content))  : null,
					props.subtitle ? h("div",{ class: "media-subtitle small" },h("small", { class: "text-muted" }, props.subtitle)) : null
				),
				position.class === "media-right" ? avatar : null
			)
		)
	}
}
dataent.Chat.Widget.MediaProfile.POSITION
=
{
	left: { class: "media-left" }, right: { class: "media-right" }
}

/**
 * @description dataent.Chat.Widget Room Component
 */
dataent.Chat.Widget.Room
=
class extends Component {
	render ( ) {
		const { props, state } = this
		const hints            =
		[
			{
				 match: /@(\w*)$/,
				search: function (keyword, callback) {
					if ( props.type === 'Group' ) {
						const query = keyword.slice(1)
						const users = [].concat(dataent._.as_array(props.owner), props.users)
						const grep  = users.filter(user => user !== dataent.session.user && user.indexOf(query) === 0)

						callback(grep)
					}
				},
				component: function (item) {
					return (
						h(dataent.Chat.Widget.MediaProfile, {
							title: dataent.user.full_name(item),
							image: dataent.user.image(item),
							 size: "small"
						})
					)
				}
			},
			{
				match: /:([a-z]*)$/,
			   search: function (keyword, callback) {
					dataent.chat.emoji(function (emojis) {
						const query = keyword.slice(1)
						const items = [ ]
						for (const emoji of emojis)
							for (const alias of emoji.aliases)
								if ( alias.indexOf(query) === 0 )
									items.push({ name: alias, value: emoji.emoji })

						callback(items)
					})
			   },
				 content: (item) => item.value,
			   component: function (item) {
					return (
						h(dataent.Chat.Widget.MediaProfile, {
							title: item.name,
							 abbr: item.value,
							 size: "small"
						})
					)
			   }
		   }
		]

		const actions = dataent._.compact([
			!dataent._.is_mobile() && {
				 icon: "camera",
				label: "Camera",
				onclick: ( ) => {
					const capture = new dataent.ui.Capture({
						animate: false,
						  error: true
					})
					capture.show()

					capture.submit(data_url => {
						// data_url
					})
				}
			},
			{
				 icon: "file",
				label: "File",
				onclick: ( ) => {
					const dialog = dataent.upload.make({
							args: { doctype: "Chat Room", docname: props.name },
						callback: (a, b, args) => {
							const { file_url, filename } = args
							dataent.chat.message.send(props.name, { path: file_url, name: filename }, "File")
						}
					})
				}
			}
		])

		if ( dataent.session.user !== 'Guest' ) {
			if (props.messages) {
				props.messages = dataent._.as_array(props.messages)
				for (const message of props.messages)
					if ( !message.seen.includes(dataent.session.user) )
						dataent.chat.message.seen(message.name)
					else
						break
			}
		}

		return (
			h("div", { class: `panel panel-default
				${props.name ? "panel-bg" : ""}
				${props.layout === dataent.Chat.Layout.PAGE || dataent._.is_mobile() ? "panel-span" : ""}`,
				style: props.layout === dataent.Chat.Layout.PAGE && { width: "75%", left: "25%", "box-shadow": "none" } },
				props.name && h(dataent.Chat.Widget.Room.Header, { ...props, on_back: props.destroy }),
				props.name ?
					!dataent._.is_empty(props.messages) ?
						h(dataent.chat.component.ChatList, {
							messages: props.messages
						})
						:
						h("div", { class: "panel-body", style: { "height": "100%" } },
							h("div", { class: "vcenter" },
								h("div", { class: "text-center text-extra-muted" },
									h(dataent.components.Octicon, { type: "comment-discussion", style: "font-size: 48px" }),
									h("p","",__("Start a conversation."))
								)
							)
						)
					:
					h("div", { class: "panel-body", style: { "height": "100%" } },
						h("div", { class: "vcenter" },
							h("div", { class: "text-center text-extra-muted" },
								h(dataent.components.Octicon, { type: "comment-discussion", style: "font-size: 125px" }),
								h("p","",__("Select a chat to start messaging."))
							)
						)
					),
				props.name ?
					h("div", { class: "chat-room-footer" },
						h(dataent.chat.component.ChatForm, { actions: actions,
							onchange: () => {
								dataent.chat.message.typing(props.name)
							},
							onsubmit: (message) => {
								dataent.chat.message.send(props.name, message)
							},
							hint: hints
						})
					)
					:
					null
			)
		)
	}
}

dataent.Chat.Widget.Room.Header
=
class extends Component {
	render ( ) {
		const { props }     = this

		const item          = { }

		if ( ["Group", "Visitor"].includes(props.type) ) {
			item.route      = `Form/Chat Room/${props.name}`

			item.title      = props.room_name
			item.image      = props.avatar

			if ( !dataent._.is_empty(props.typing) ) {
				props.typing  = dataent._.as_array(props.typing) // HACK: (BUG) why does typing return as a string?
				const users   = props.typing.map(user => dataent.user.first_name(user))
				item.subtitle = `${users.join(", ")} typing...`
			} else
				item.subtitle = props.type === "Group" ?
					__(`${props.users.length} ${dataent._.pluralize('member', props.users.length)}`)
					:
					""
		}
		else {
			const user      = props.owner === dataent.session.user ? dataent._.squash(props.users) : props.owner

			item.route      = `Form/User/${user}`

			item.title      = dataent.user.full_name(user)
			item.image      = dataent.user.image(user)

			if ( !dataent._.is_empty(props.typing) )
				item.subtitle = 'typing...'
		}

		const popper        = props.layout === dataent.Chat.Layout.POPPER || dataent._.is_mobile()

		return (
			h("div", { class: "panel-heading", style: { "height": "50px" } }, // sorry. :(
				h("div", { class: "level" },
					popper && dataent.session.user !== "Guest" ?
						h(dataent.components.Button,{class:"btn-back",onclick:props.on_back},
							h(dataent.components.Octicon, { type: "chevron-left" })
						) : null,
					h("div","",
						h("div", { class: "panel-title" },
							h("div", { class: "cursor-pointer", onclick: () => { dataent.set_route(item.route) }},
								h(dataent.Chat.Widget.MediaProfile, { ...item })
							)
						)
					),
					h("div", { class: popper ? "col-xs-1"  : "col-xs-3" },
						h("div", { class: "text-right" },

						)
					)
				)
			)
		)
	}
}

/**
 * @description ChatList Component
 *
 * @prop {array} messages - ChatMessage(s)
 */
dataent.chat.component.ChatList
=
class extends Component {
	on_mounted ( ) {
		this.$element  = $('.dataent-chat').find('.chat-list')
		this.$element.scrollTop(this.$element[0].scrollHeight)
	}

	on_updated ( ) {
		this.$element.scrollTop(this.$element[0].scrollHeight)
	}

	render ( ) {
		var messages = [ ]
		for (var i   = 0 ; i < this.props.messages.length ; ++i) {
			var   message   = this.props.messages[i]
			const me        = message.user === dataent.session.user

			if ( i === 0 || !dataent.datetime.equal(message.creation, this.props.messages[i - 1].creation, 'day') )
				messages.push({ type: "Notification", content: message.creation.format('MMMM DD') })

			messages.push(message)
		}

		return (
			h("div",{class:"chat-list list-group"},
				!dataent._.is_empty(messages) ?
					messages.map(m => h(dataent.chat.component.ChatList.Item, {...m})) : null
			)
		)
	}
}

/**
 * @description ChatList.Item Component
 *
 * @prop {string} name       - ChatMessage name
 * @prop {string} user       - ChatMessage user
 * @prop {string} room       - ChatMessage room
 * @prop {string} room_type  - ChatMessage room_type ("Direct", "Group" or "Visitor")
 * @prop {string} content    - ChatMessage content
 * @prop {dataent.datetime.datetime} creation - ChatMessage creation
 *
 * @prop {boolean} groupable - Whether the ChatMessage is groupable.
 */
dataent.chat.component.ChatList.Item
=
class extends Component {
	render ( ) {
		const { props } = this

		const me        = props.user === dataent.session.user
		const content   = props.content

		return (
			h("div",{class: "chat-list-item list-group-item"},
				props.type === "Notification" ?
					h("div",{class:"chat-list-notification"},
						h("div",{class:"chat-list-notification-content"},
							content
						)
					)
					:
					h("div",{class:`${me ? "text-right" : ""}`},
						props.room_type === "Group" && !me ?
							h(dataent.components.Avatar, {
								title: dataent.user.full_name(props.user),
								image: dataent.user.image(props.user)
							}) : null,
						h(dataent.chat.component.ChatBubble, props)
					)
			)
		)
	}
}

/**
 * @description ChatBubble Component
 *
 * @prop {string} name       - ChatMessage name
 * @prop {string} user       - ChatMessage user
 * @prop {string} room       - ChatMessage room
 * @prop {string} room_type  - ChatMessage room_type ("Direct", "Group" or "Visitor")
 * @prop {string} content    - ChatMessage content
 * @prop {dataent.datetime.datetime} creation - ChatMessage creation
 *
 * @prop {boolean} groupable - Whether the ChatMessage is groupable.
 */
dataent.chat.component.ChatBubble
=
class extends Component {
	constructor (props) {
		super (props)

		this.onclick = this.onclick.bind(this)
	}

	onclick ( ) {
		const { props } = this
		if ( props.user === dataent.session.user ) {
			dataent.quick_edit("Chat Message", props.name, (values) => {

			})
		}
	}

	render  ( ) {
		const { props } = this
		const creation 	= props.creation.format('hh:mm A')

		const me        = props.user === dataent.session.user
		const read      = !dataent._.is_empty(props.seen) && !props.seen.includes(dataent.session.user)

		const content   = props.content

		return (
			h("div",{class:`chat-bubble ${props.groupable ? "chat-groupable" : ""} chat-bubble-${me ? "r" : "l"}`,
				onclick: this.onclick},
				props.room_type === "Group" && !me?
					h("div",{class:"chat-bubble-author"},
						h("a", { onclick: () => { dataent.set_route(`Form/User/${props.user}`) } },
							dataent.user.full_name(props.user)
						)
					) : null,
				h("div",{class:"chat-bubble-content"},
						h("small","",
							props.type === "File" ?
								h("a", { class: "no-decoration", href: content.path, target: "_blank" },
									h(dataent.components.FontAwesome, { type: "file", fixed: true }), ` ${content.name}`
								)
								:
								content
						)
				),
				h("div",{class:"chat-bubble-meta"},
					h("span",{class:"chat-bubble-creation"},creation),
					me && read ?
						h("span",{class:"chat-bubble-check"},
							h(dataent.components.Octicon,{type:"check"})
						) : null
				)
			)
		)
	}
}

/**
 * @description ChatForm Component
 */
dataent.chat.component.ChatForm
=
class extends Component {
	constructor (props) {
		super (props)

		this.onchange   = this.onchange.bind(this)
		this.onsubmit   = this.onsubmit.bind(this)

		this.hint        = this.hint.bind(this)

		this.state       = dataent.chat.component.ChatForm.defaultState
	}

	onchange (e) {
		const { props, state } = this
		const value            = e.target.value

		this.set_state({
			[e.target.name]: value
		})

		props.onchange(state)

		this.hint(value)
	}

	hint (value) {
		const { props, state } = this

		if ( props.hint ) {
			const tokens =  value.split(" ")
			const sliced = tokens.slice(0, tokens.length - 1)

			const token  = tokens[tokens.length - 1]

			if ( token ) {
				props.hint   = dataent._.as_array(props.hint)
				const hint   = props.hint.find(hint => hint.match.test(token))

				if ( hint ) {
					hint.search(token, items => {
						const hints = items.map(item => {
							// You should stop writing one-liners! >_>
							const replace = token.replace(hint.match, hint.content ? hint.content(item) : item)
							const content = `${sliced.join(" ")} ${replace}`.trim()
							item          = { component: hint.component(item), content: content }

							return item
						}).slice(0, hint.max || 5)

						this.set_state({ hints })
					})
				}
				else
					this.set_state({ hints: [ ] })
			} else
				this.set_state({ hints: [ ] })
		}
	}

	onsubmit (e) {
		e.preventDefault()

		if ( this.state.content ) {
			this.props.onsubmit(this.state.content)

			this.set_state({ content: null })
		}
	}

	render ( ) {
		const { props, state } = this

		return (
			h("div",{class:"chat-form"},
				state.hints.length ?
					h("ul", { class: "hint-list list-group" },
						state.hints.map((item) => {
							return (
								h("li", { class: "hint-list-item list-group-item" },
									h("a", { href: "javascript:void(0)", onclick: () => {
										this.set_state({ content: item.content, hints: [ ] })
									}},
										item.component
									)
								)
							)
						})
					) : null,
				h("form", { oninput: this.onchange, onsubmit: this.onsubmit },
					h("div",{class:"input-group input-group-lg"},
						!dataent._.is_empty(props.actions) ?
							h("div",{class:"input-group-btn dropup"},
								h(dataent.components.Button,{ class: "dropdown-toggle", "data-toggle": "dropdown"},
									h(dataent.components.FontAwesome, { class: "text-muted", type: "paperclip", fixed: true })
								),
								h("div",{ class:"dropdown-menu dropdown-menu-left", onclick: e => e.stopPropagation() },
									!dataent._.is_empty(props.actions) && props.actions.map((action) => {
										return (
											h("li", null,
												h("a",{onclick:action.onclick},
													h(dataent.components.FontAwesome,{type:action.icon,fixed:true}), ` ${action.label}`,
												)
											)
										)
									})
								)
							) : null,
						h("textarea", {
									class: "form-control",
									 name: "content",
									value: state.content,
							  placeholder: "Type a message",
								autofocus: true,
							   onkeypress: (e) => {
									if ( e.which === dataent.ui.keycode.RETURN && !e.shiftKey )
										this.onsubmit(e)
							   }
						}),
						h("div",{class:"input-group-btn"},
							h(dataent.components.Button, { onclick: this.onsubmit },
								h(dataent.components.FontAwesome, { class: !dataent._.is_empty(state.content) ? "text-primary" : "text-muted", type: "send", fixed: true })
							),
						)
					)
				)
			)
		)
	}
}
dataent.chat.component.ChatForm.defaultState
=
{
	content: null,
	  hints: [ ],
}

/**
 * @description EmojiPicker Component
 *
 * @todo Under Development
 */
dataent.chat.component.EmojiPicker
=
class extends Component  {
	render ( ) {
		const { props } = this

		return (
			h("div", { class: `dataent-chat-emoji dropup ${props.class}` },
				h(dataent.components.Button, { type: "primary", class: "dropdown-toggle", "data-toggle": "dropdown" },
					h(dataent.components.FontAwesome, { type: "smile-o", fixed: true })
				),
				h("div", { class: "dropdown-menu dropdown-menu-right", onclick: e => e.stopPropagation() },
					h("div", { class: "panel panel-default" },
						h(dataent.chat.component.EmojiPicker.List)
					)
				)
			)
		)
	}
}
dataent.chat.component.EmojiPicker.List
=
class extends Component {
	render ( ) {
		const { props } = this

		return (
			h("div", { class: "list-group" },

			)
		)
	}
}

/**
 * @description Python equivalent to sys.platform
 */
dataent.provide('dataent._')
dataent._.platform   = () => {
	const string    = navigator.appVersion

	if ( string.includes("Win") ) 	return "Windows"
	if ( string.includes("Mac") ) 	return "Darwin"
	if ( string.includes("X11") ) 	return "UNIX"
	if ( string.includes("Linux") ) return "Linux"

	return undefined
}

/**
 * @description Dataent's Asset Helper
 */
dataent.provide('dataent.assets')
dataent.assets.image = (image, app = 'dataent') => {
	const  path     = `/assets/${app}/images/${image}`
	return path
}

/**
 * @description Notify using Web Push Notifications
 */
dataent.provide('dataent.boot')
dataent.provide('dataent.browser')
dataent.browser.Notification = 'Notification' in window

dataent.notify     = (string, options) => {
	dataent.log    = dataent.Logger.get('dataent.notify')

	const OPTIONS = {
		icon: dataent.assets.image('favicon.png', 'dataent'),
		lang: dataent.boot.lang || "en"
	}
	options       = Object.assign({ }, OPTIONS, options)

	if ( !dataent.browser.Notification )
		dataent.log.error('ERROR: This browser does not support desktop notifications.')

	Notification.requestPermission(status => {
		if ( status === "granted" ) {
			const notification = new Notification(string, options)
		}
	})
}

dataent.chat.render = (render = true, force = false) =>
{
	dataent.log.info(`${render ? "Enable" : "Disable"} Chat for User.`)

	const desk = 'desk' in dataent
	if ( desk ) {
		// With the assumption, that there's only one navbar.
		const $placeholder = $('.navbar .dataent-chat-dropdown')

		// Render if dataent-chat-toggle doesn't exist.
		if ( dataent.utils.is_empty($placeholder.has('.dataent-chat-toggle')) ) {
			const $template = $(`
				<a class="dropdown-toggle dataent-chat-toggle" data-toggle="dropdown">
					<div>
						<i class="octicon octicon-comment-discussion"/>
					</div>
				</a>
			`)

			$placeholder.addClass('dropdown hidden')
			$placeholder.html($template)
		}

		if ( render ) {
			$placeholder.removeClass('hidden')
		} else {
			$placeholder.addClass('hidden')
		}
	}

	// Avoid re-renders. Once is enough.
	if ( !dataent.chatter || force ) {
		dataent.chatter = new dataent.Chat({
			target: desk ? '.navbar .dataent-chat-toggle' : null
		})

		if ( render ) {
			if ( dataent.session.user === 'Guest' && !desk ) {
				dataent.store = dataent.Store.get('dataent.chat')
				var token	 = dataent.store.get('guest_token')

				dataent.log.info(`Local Guest Token - ${token}`)

				const setup_room = (token) =>
				{
					return new Promise(resolve => {
						dataent.chat.room.create("Visitor", token).then(room => {
							dataent.log.info(`Visitor Room Created: ${room.name}`)
							dataent.chat.room.subscribe(room.name)

							var reference = room

							dataent.chat.room.history(room.name).then(messages => {
								const  room = { ...reference, messages: messages }
								return room
							}).then(room => {
								resolve(room)
							})
						})
					})
				}

				if ( !token ) {
					dataent.chat.website.token().then(token => {
						dataent.log.info(`Generated Guest Token - ${token}`)
						dataent.store.set('guest_token', token)

						setup_room(token).then(room => {
							dataent.chatter.render({ room })
						})
					})
				} else {
					setup_room(token).then(room => {
						dataent.chatter.render({ room })
					})
				}
			} else {
				dataent.chatter.render()
			}
		}
	}
}

dataent.chat.setup  = () => {
	dataent.log     = dataent.Logger.get('dataent.chat')

	dataent.log.info('Setting up dataent.chat')
	dataent.log.warn('TODO: dataent.chat.<object> requires a storage.')

	if ( dataent.session.user !== 'Guest' ) {
		// Create/Get Chat Profile for session User, retrieve enable_chat
		dataent.log.info('Creating a Chat Profile.')

		dataent.chat.profile.create('enable_chat').then(({ enable_chat }) => {
			dataent.log.info(`Chat Profile created for User ${dataent.session.user}.`)

			if ( 'desk' in dataent ) { // same as desk?
				const should_render = Boolean(parseInt(dataent.sys_defaults.enable_chat)) && enable_chat
				dataent.chat.render(should_render)
			}
		})

		// Triggered when a User updates his/her Chat Profile.
		// Don't worry, enable_chat is broadcasted to this user only. No overhead. :)
		dataent.chat.profile.on.update((user, profile) => {
			if ( user === dataent.session.user && 'enable_chat' in profile ) {
				dataent.log.warn(`Chat Profile update (Enable Chat - ${Boolean(profile.enable_chat)})`)
				const should_render = Boolean(parseInt(dataent.sys_defaults.enable_chat)) && profile.enable_chat
				dataent.chat.render(should_render)
			}
		})
	} else {
		// Website Settings
		dataent.log.info('Retrieving Chat Website Settings.')
		dataent.chat.website.settings(["socketio", "enable", "enable_from", "enable_to"])
			.then(settings => {
				dataent.log.info(`Chat Website Setting - ${JSON.stringify(settings)}`)
				dataent.log.info(`Chat Website Setting - ${settings.enable ? "Enable" : "Disable"}`)

				var should_render = settings.enable
				if ( settings.enable_from && settings.enable_to ) {
					dataent.log.info(`Enabling Chat Schedule - ${settings.enable_from.format()} : ${settings.enable_to.format()}`)

					const range   = new dataent.datetime.range(settings.enable_from, settings.enable_to)
					should_render = range.contains(dataent.datetime.now())
				}

				if ( should_render ) {
					dataent.log.info("Initializing Socket.IO")
					dataent.socketio.init(settings.socketio.port)
				}

				dataent.chat.render(should_render)
		})
	}
}

$(document).on('ready toolbar_setup', () =>
{
	dataent.chat.setup()
})
