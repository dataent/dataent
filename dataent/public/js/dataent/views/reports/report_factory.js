// Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

dataent.views.ReportFactory = class ReportFactory extends dataent.views.Factory {
	make(route) {
		const _route = ['List', route[1], 'Report'];

		if (route[2]) {
			// custom report
			_route.push(route[2]);
		}

		dataent.set_route(_route);
	}
}
