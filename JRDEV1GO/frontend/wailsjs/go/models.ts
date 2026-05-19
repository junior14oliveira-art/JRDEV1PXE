export namespace license {
	
	export class ActivateResult {
	    success: boolean;
	    message: string;
	
	    static createFrom(source: any = {}) {
	        return new ActivateResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.success = source["success"];
	        this.message = source["message"];
	    }
	}
	export class Info {
	    key: string;
	    machine_id: string;
	    expiry: string;
	    days_left: number;
	    activated: string;
	    developer: boolean;
	
	    static createFrom(source: any = {}) {
	        return new Info(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.key = source["key"];
	        this.machine_id = source["machine_id"];
	        this.expiry = source["expiry"];
	        this.days_left = source["days_left"];
	        this.activated = source["activated"];
	        this.developer = source["developer"];
	    }
	}
	export class Status {
	    code: string;
	    message: string;
	    days_left: number;
	    expiry: string;
	    developer: boolean;
	
	    static createFrom(source: any = {}) {
	        return new Status(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.code = source["code"];
	        this.message = source["message"];
	        this.days_left = source["days_left"];
	        this.expiry = source["expiry"];
	        this.developer = source["developer"];
	    }
	}

}

export namespace pxe {
	
	export class StartResult {
	    success: boolean;
	    message: string;
	
	    static createFrom(source: any = {}) {
	        return new StartResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.success = source["success"];
	        this.message = source["message"];
	    }
	}

}

export namespace system {
	
	export class CommandResult {
	    success: boolean;
	    output: string;
	    error: string;
	
	    static createFrom(source: any = {}) {
	        return new CommandResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.success = source["success"];
	        this.output = source["output"];
	        this.error = source["error"];
	    }
	}
	export class NetworkInterface {
	    name: string;
	    ip: string;
	    mask: string;
	
	    static createFrom(source: any = {}) {
	        return new NetworkInterface(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.ip = source["ip"];
	        this.mask = source["mask"];
	    }
	}
	export class SystemInfo {
	    os: string;
	    arch: string;
	    dism_found: boolean;
	    dism_path: string;
	    seven_zip: string;
	    oscdimg: string;
	    free_space_gb: number;
	    total_ram_gb: number;
	
	    static createFrom(source: any = {}) {
	        return new SystemInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.os = source["os"];
	        this.arch = source["arch"];
	        this.dism_found = source["dism_found"];
	        this.dism_path = source["dism_path"];
	        this.seven_zip = source["seven_zip"];
	        this.oscdimg = source["oscdimg"];
	        this.free_space_gb = source["free_space_gb"];
	        this.total_ram_gb = source["total_ram_gb"];
	    }
	}

}

