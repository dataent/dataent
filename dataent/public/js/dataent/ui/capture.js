// dataent.ui.Capture
// Author - Achilles Rasquinha <achilles@epaas.xyz>

/**
 * @description Converts a canvas, image or a video to a data URL string.
 * 
 * @param 	{HTMLElement} element - canvas, img or video.
 * @returns {string} 			  - The data URL string.
 * 
 * @example
 * dataent._.get_data_uri(video)
 * // returns "data:image/pngbase64,..."
 */
dataent._.get_data_uri = element =>
{
	const $element = $(element)
	const width    = $element.width()
	const height   = $element.height()

	const $canvas     = $('<canvas/>')
	$canvas[0].width  = width
	$canvas[0].height = height

	const context     = $canvas[0].getContext('2d')
	context.drawImage($element[0], 0, 0, width, height)
	
	const data_uri = $canvas[0].toDataURL('image/png')

	return data_uri
}

/**
 * @description Dataent's Capture object.
 * 
 * @example
 * const capture = dataent.ui.Capture()
 * capture.show()
 * 
 * capture.click((data_uri) => {
 * 	// do stuff
 * })
 * 
 * @see https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Taking_still_photos
 */
dataent.ui.Capture = class
{
	constructor (options = { })
	{
		this.options = dataent.ui.Capture.OPTIONS
		this.set_options(options)
	}
	
	set_options (options)
	{
		this.options = { ...dataent.ui.Capture.OPTIONS, ...options }
		
		return this
	}
	
	render ( )
	{
		return navigator.mediaDevices.getUserMedia({ video: true }).then(stream =>
		{
			this.dialog 	 = new dataent.ui.Dialog({
				  title: this.options.title,
				animate: this.options.animate,
				 action:
				{
					secondary:
					{
						label: "<b>&times</b>"
					}
				}
			})
	
			const $e 		 = $(dataent.ui.Capture.TEMPLATE)
			
			const video      = $e.find('video')[0]
			video.srcObject  = stream
			video.play()
			
			const $container = $(this.dialog.body)
			$container.html($e)
			
			$e.find('.fc-btf').hide()

			$e.find('.fc-bcp').click(() =>
			{
				const data_url = dataent._.get_data_uri(video)
				$e.find('.fc-p').attr('src', data_url)

				$e.find('.fc-s').hide()
				$e.find('.fc-p').show()

				$e.find('.fc-btu').hide()
				$e.find('.fc-btf').show()
			})

			$e.find('.fc-br').click(() =>
			{
				$e.find('.fc-p').hide()
				$e.find('.fc-s').show()

				$e.find('.fc-btf').hide()
				$e.find('.fc-btu').show()
			})

			$e.find('.fc-bs').click(() =>
			{
				const data_url = dataent._.get_data_uri(video)
				this.hide()
				
				if (this.callback)
					this.callback(data_url)
			})
		})
	}

	show ( )
	{
		this.render().then(() =>
		{
			this.dialog.show()
		}).catch(err => {
			if ( this.options.error )
			{
				const alert = `<span class="indicator red"/> ${dataent.ui.Capture.ERR_MESSAGE}`
				dataent.show_alert(alert, 3)
			}

			throw err
		})
	}

	hide ( )
	{
		if ( this.dialog )
			this.dialog.hide()
	}

	submit (fn)
	{
		this.callback = fn
	}
}
dataent.ui.Capture.OPTIONS =
{
	  title: __(`Camera`),
	animate: false,
	  error: false,
}
dataent.ui.Capture.ERR_MESSAGE = __("Unable to load camera.")
dataent.ui.Capture.TEMPLATE 	  =
`
<div class="dataent-capture">
	<div class="panel panel-default">
		<img class="fc-p img-responsive"/>
		<div class="fc-s  embed-responsive embed-responsive-16by9">
			<video class="embed-responsive-item">${dataent.ui.Capture.ERR_MESSAGE}</video>
		</div>
	</div>
	<div>
		<div class="fc-btf">
			<div class="row">
				<div class="col-md-6">
					<div class="pull-left">
						<button class="btn btn-default fc-br">
							<small>${__('Retake')}</small>
						</button>
					</div>
				</div>
				<div class="col-md-6">
					<div class="pull-right">
						<button class="btn btn-primary fc-bs">
							<small>${__('Submit')}</small>
						</button>
					</div>
				</div>
			</div>
		</div>
		<div class="fc-btu">
			<div class="row">
				<div class="col-md-6">
					${
						''
						// <div class="pull-left">
						// 	<button class="btn btn-default">
						// 		<small>${__('Take Video')}</small>
						// 	</button>
						// </div>
					}
				</div>
				<div class="col-md-6">
					<div class="pull-right">
						<button class="btn btn-default fc-bcp">
							<small>${__('Take Photo')}</small>
						</button>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
`