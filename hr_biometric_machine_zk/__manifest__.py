{
    "name" : "ZK Biometric Device Integration Kware (ZKTECO) 13",
    "version" : "1.1",
    "author" : "JUVENTUD PRODUCTIVA VENEZOLANA",
    "category" : "HR",
    "website" : "https://www.youtube.com/channel/UCTj66IUz5M-QV15Mtbx_7yg",
    "description": "Module for the integration between ZK Biometric Machines and Odoo.",
    'license': 'AGPL-3',
    "depends" : ["base","hr",'hr_attendance'],
    "data" : [
				"wizard/zk_create_users_wizard.xml",
				"views/biometric_machine_view.xml",
				"secuirty/res_groups.xml",
				"secuirty/ir.model.access.csv"
			],
	'images': ['static/images/zk_screenshot.gif'],
    "active": True,
    "installable": True,
    'currency': 'EUR',
    'price': 99.00,
}
