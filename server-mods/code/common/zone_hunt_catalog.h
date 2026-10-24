#pragma once
#include <cstdint>
namespace NightcapHunt {
inline bool IsAugment(uint32_t id) { if ((id>=961000 && id<=961003) || (id>=961020 && id<=961023)) { return true; } switch (id) {
case 940024:
case 940025:
case 940026:
case 940027:
case 940032:
case 940033:
case 940034:
case 940035:
case 940040:
case 940041:
case 940042:
case 940043:
case 940072:
case 940073:
case 940074:
case 940075:
case 940080:
case 940081:
case 940082:
case 940083:
case 940088:
case 940089:
case 940090:
case 940091:
case 940096:
case 940097:
case 940098:
case 940099:
case 940104:
case 940105:
case 940106:
case 940107:
case 940112:
case 940113:
case 940114:
case 940115:
case 940120:
case 940121:
case 940122:
case 940123:
case 940128:
case 940129:
case 940130:
case 940131:
case 940144:
case 940145:
case 940146:
case 940147:
case 940152:
case 940153:
case 940154:
case 940155:
case 940160:
case 940161:
case 940162:
case 940163:
case 940184:
case 940185:
case 940186:
case 940187:
case 940192:
case 940193:
case 940194:
case 940195:
case 940208:
case 940209:
case 940210:
case 940211:
case 940216:
case 940217:
case 940218:
case 940219:
case 940224:
case 940225:
case 940226:
case 940227:
case 940232:
case 940233:
case 940234:
case 940235:
case 940240:
case 940241:
case 940242:
case 940243:
case 940248:
case 940249:
case 940250:
case 940251:
case 940256:
case 940257:
case 940258:
case 940259:
case 940264:
case 940265:
case 940266:
case 940267:
case 940272:
case 940273:
case 940274:
case 940275:
case 940280:
case 940281:
case 940282:
case 940283:
case 940312:
case 940313:
case 940314:
case 940315:
case 940320:
case 940321:
case 940322:
case 940323:
case 940328:
case 940329:
case 940330:
case 940331:
case 940336:
case 940337:
case 940338:
case 940339:
case 940344:
case 940345:
case 940346:
case 940347:
case 940360:
case 940361:
case 940362:
case 940363:
case 940368:
case 940369:
case 940370:
case 940371:
case 940384:
case 940385:
case 940386:
case 940387:
case 940400:
case 940401:
case 940402:
case 940403:
case 940408:
case 940409:
case 940410:
case 940411:
case 940416:
case 940417:
case 940418:
case 940419:
case 940424:
case 940425:
case 940426:
case 940427:
case 940456:
case 940457:
case 940458:
case 940459:
case 940464:
case 940465:
case 940466:
case 940467:
case 940472:
case 940473:
case 940474:
case 940475:
case 940480:
case 940481:
case 940482:
case 940483:
case 940496:
case 940497:
case 940498:
case 940499:
case 940504:
case 940505:
case 940506:
case 940507:
case 940512:
case 940513:
case 940514:
case 940515:
case 940520:
case 940521:
case 940522:
case 940523:
case 940528:
case 940529:
case 940530:
case 940531:
case 940536:
case 940537:
case 940538:
case 940539:
case 940544:
case 940545:
case 940546:
case 940547:
case 940560:
case 940561:
case 940562:
case 940563:
case 940568:
case 940569:
case 940570:
case 940571:
case 940576:
case 940577:
case 940578:
case 940579:
case 940584:
case 940585:
case 940586:
case 940587:
case 940592:
case 940593:
case 940594:
case 940595:
case 940600:
case 940601:
case 940602:
case 940603:
case 940608:
case 940609:
case 940610:
case 940611:
return true; default: return false; } }
inline uint32_t NextTier(uint32_t id) { if ((id>=961000 && id<961003) || (id>=961020 && id<961023)) { return id+1; } switch (id) {
case 940024: return 940025;
case 940025: return 940026;
case 940026: return 940027;
case 940028: return 940029;
case 940029: return 940030;
case 940030: return 940031;
case 940032: return 940033;
case 940033: return 940034;
case 940034: return 940035;
case 940036: return 940037;
case 940037: return 940038;
case 940038: return 940039;
case 940040: return 940041;
case 940041: return 940042;
case 940042: return 940043;
case 940044: return 940045;
case 940045: return 940046;
case 940046: return 940047;
case 940072: return 940073;
case 940073: return 940074;
case 940074: return 940075;
case 940076: return 940077;
case 940077: return 940078;
case 940078: return 940079;
case 940080: return 940081;
case 940081: return 940082;
case 940082: return 940083;
case 940084: return 940085;
case 940085: return 940086;
case 940086: return 940087;
case 940088: return 940089;
case 940089: return 940090;
case 940090: return 940091;
case 940092: return 940093;
case 940093: return 940094;
case 940094: return 940095;
case 940096: return 940097;
case 940097: return 940098;
case 940098: return 940099;
case 940100: return 940101;
case 940101: return 940102;
case 940102: return 940103;
case 940104: return 940105;
case 940105: return 940106;
case 940106: return 940107;
case 940108: return 940109;
case 940109: return 940110;
case 940110: return 940111;
case 940112: return 940113;
case 940113: return 940114;
case 940114: return 940115;
case 940116: return 940117;
case 940117: return 940118;
case 940118: return 940119;
case 940120: return 940121;
case 940121: return 940122;
case 940122: return 940123;
case 940124: return 940125;
case 940125: return 940126;
case 940126: return 940127;
case 940128: return 940129;
case 940129: return 940130;
case 940130: return 940131;
case 940132: return 940133;
case 940133: return 940134;
case 940134: return 940135;
case 940144: return 940145;
case 940145: return 940146;
case 940146: return 940147;
case 940148: return 940149;
case 940149: return 940150;
case 940150: return 940151;
case 940152: return 940153;
case 940153: return 940154;
case 940154: return 940155;
case 940156: return 940157;
case 940157: return 940158;
case 940158: return 940159;
case 940160: return 940161;
case 940161: return 940162;
case 940162: return 940163;
case 940164: return 940165;
case 940165: return 940166;
case 940166: return 940167;
case 940184: return 940185;
case 940185: return 940186;
case 940186: return 940187;
case 940188: return 940189;
case 940189: return 940190;
case 940190: return 940191;
case 940192: return 940193;
case 940193: return 940194;
case 940194: return 940195;
case 940196: return 940197;
case 940197: return 940198;
case 940198: return 940199;
case 940208: return 940209;
case 940209: return 940210;
case 940210: return 940211;
case 940212: return 940213;
case 940213: return 940214;
case 940214: return 940215;
case 940216: return 940217;
case 940217: return 940218;
case 940218: return 940219;
case 940220: return 940221;
case 940221: return 940222;
case 940222: return 940223;
case 940224: return 940225;
case 940225: return 940226;
case 940226: return 940227;
case 940228: return 940229;
case 940229: return 940230;
case 940230: return 940231;
case 940232: return 940233;
case 940233: return 940234;
case 940234: return 940235;
case 940236: return 940237;
case 940237: return 940238;
case 940238: return 940239;
case 940240: return 940241;
case 940241: return 940242;
case 940242: return 940243;
case 940244: return 940245;
case 940245: return 940246;
case 940246: return 940247;
case 940248: return 940249;
case 940249: return 940250;
case 940250: return 940251;
case 940252: return 940253;
case 940253: return 940254;
case 940254: return 940255;
case 940256: return 940257;
case 940257: return 940258;
case 940258: return 940259;
case 940260: return 940261;
case 940261: return 940262;
case 940262: return 940263;
case 940264: return 940265;
case 940265: return 940266;
case 940266: return 940267;
case 940268: return 940269;
case 940269: return 940270;
case 940270: return 940271;
case 940272: return 940273;
case 940273: return 940274;
case 940274: return 940275;
case 940276: return 940277;
case 940277: return 940278;
case 940278: return 940279;
case 940280: return 940281;
case 940281: return 940282;
case 940282: return 940283;
case 940284: return 940285;
case 940285: return 940286;
case 940286: return 940287;
case 940312: return 940313;
case 940313: return 940314;
case 940314: return 940315;
case 940316: return 940317;
case 940317: return 940318;
case 940318: return 940319;
case 940320: return 940321;
case 940321: return 940322;
case 940322: return 940323;
case 940324: return 940325;
case 940325: return 940326;
case 940326: return 940327;
case 940328: return 940329;
case 940329: return 940330;
case 940330: return 940331;
case 940332: return 940333;
case 940333: return 940334;
case 940334: return 940335;
case 940336: return 940337;
case 940337: return 940338;
case 940338: return 940339;
case 940340: return 940341;
case 940341: return 940342;
case 940342: return 940343;
case 940344: return 940345;
case 940345: return 940346;
case 940346: return 940347;
case 940348: return 940349;
case 940349: return 940350;
case 940350: return 940351;
case 940360: return 940361;
case 940361: return 940362;
case 940362: return 940363;
case 940364: return 940365;
case 940365: return 940366;
case 940366: return 940367;
case 940368: return 940369;
case 940369: return 940370;
case 940370: return 940371;
case 940372: return 940373;
case 940373: return 940374;
case 940374: return 940375;
case 940384: return 940385;
case 940385: return 940386;
case 940386: return 940387;
case 940388: return 940389;
case 940389: return 940390;
case 940390: return 940391;
case 940400: return 940401;
case 940401: return 940402;
case 940402: return 940403;
case 940404: return 940405;
case 940405: return 940406;
case 940406: return 940407;
case 940408: return 940409;
case 940409: return 940410;
case 940410: return 940411;
case 940412: return 940413;
case 940413: return 940414;
case 940414: return 940415;
case 940416: return 940417;
case 940417: return 940418;
case 940418: return 940419;
case 940420: return 940421;
case 940421: return 940422;
case 940422: return 940423;
case 940424: return 940425;
case 940425: return 940426;
case 940426: return 940427;
case 940428: return 940429;
case 940429: return 940430;
case 940430: return 940431;
case 940456: return 940457;
case 940457: return 940458;
case 940458: return 940459;
case 940460: return 940461;
case 940461: return 940462;
case 940462: return 940463;
case 940464: return 940465;
case 940465: return 940466;
case 940466: return 940467;
case 940468: return 940469;
case 940469: return 940470;
case 940470: return 940471;
case 940472: return 940473;
case 940473: return 940474;
case 940474: return 940475;
case 940476: return 940477;
case 940477: return 940478;
case 940478: return 940479;
case 940480: return 940481;
case 940481: return 940482;
case 940482: return 940483;
case 940484: return 940485;
case 940485: return 940486;
case 940486: return 940487;
case 940496: return 940497;
case 940497: return 940498;
case 940498: return 940499;
case 940500: return 940501;
case 940501: return 940502;
case 940502: return 940503;
case 940504: return 940505;
case 940505: return 940506;
case 940506: return 940507;
case 940508: return 940509;
case 940509: return 940510;
case 940510: return 940511;
case 940512: return 940513;
case 940513: return 940514;
case 940514: return 940515;
case 940516: return 940517;
case 940517: return 940518;
case 940518: return 940519;
case 940520: return 940521;
case 940521: return 940522;
case 940522: return 940523;
case 940524: return 940525;
case 940525: return 940526;
case 940526: return 940527;
case 940528: return 940529;
case 940529: return 940530;
case 940530: return 940531;
case 940532: return 940533;
case 940533: return 940534;
case 940534: return 940535;
case 940536: return 940537;
case 940537: return 940538;
case 940538: return 940539;
case 940540: return 940541;
case 940541: return 940542;
case 940542: return 940543;
case 940544: return 940545;
case 940545: return 940546;
case 940546: return 940547;
case 940548: return 940549;
case 940549: return 940550;
case 940550: return 940551;
case 940560: return 940561;
case 940561: return 940562;
case 940562: return 940563;
case 940564: return 940565;
case 940565: return 940566;
case 940566: return 940567;
case 940568: return 940569;
case 940569: return 940570;
case 940570: return 940571;
case 940572: return 940573;
case 940573: return 940574;
case 940574: return 940575;
case 940576: return 940577;
case 940577: return 940578;
case 940578: return 940579;
case 940580: return 940581;
case 940581: return 940582;
case 940582: return 940583;
case 940584: return 940585;
case 940585: return 940586;
case 940586: return 940587;
case 940588: return 940589;
case 940589: return 940590;
case 940590: return 940591;
case 940592: return 940593;
case 940593: return 940594;
case 940594: return 940595;
case 940596: return 940597;
case 940597: return 940598;
case 940598: return 940599;
case 940600: return 940601;
case 940601: return 940602;
case 940602: return 940603;
case 940604: return 940605;
case 940605: return 940606;
case 940606: return 940607;
case 940608: return 940609;
case 940609: return 940610;
case 940610: return 940611;
case 940612: return 940613;
case 940613: return 940614;
case 940614: return 940615;
default: return 0; } }
inline bool IsReward(uint32_t id) { if ((id>=961000 && id<=961003) || (id>=961020 && id<=961023)) { return true; } switch (id) {
case 940024:
case 940025:
case 940026:
case 940027:
case 940028:
case 940029:
case 940030:
case 940031:
case 940032:
case 940033:
case 940034:
case 940035:
case 940036:
case 940037:
case 940038:
case 940039:
case 940040:
case 940041:
case 940042:
case 940043:
case 940044:
case 940045:
case 940046:
case 940047:
case 940072:
case 940073:
case 940074:
case 940075:
case 940076:
case 940077:
case 940078:
case 940079:
case 940080:
case 940081:
case 940082:
case 940083:
case 940084:
case 940085:
case 940086:
case 940087:
case 940088:
case 940089:
case 940090:
case 940091:
case 940092:
case 940093:
case 940094:
case 940095:
case 940096:
case 940097:
case 940098:
case 940099:
case 940100:
case 940101:
case 940102:
case 940103:
case 940104:
case 940105:
case 940106:
case 940107:
case 940108:
case 940109:
case 940110:
case 940111:
case 940112:
case 940113:
case 940114:
case 940115:
case 940116:
case 940117:
case 940118:
case 940119:
case 940120:
case 940121:
case 940122:
case 940123:
case 940124:
case 940125:
case 940126:
case 940127:
case 940128:
case 940129:
case 940130:
case 940131:
case 940132:
case 940133:
case 940134:
case 940135:
case 940144:
case 940145:
case 940146:
case 940147:
case 940148:
case 940149:
case 940150:
case 940151:
case 940152:
case 940153:
case 940154:
case 940155:
case 940156:
case 940157:
case 940158:
case 940159:
case 940160:
case 940161:
case 940162:
case 940163:
case 940164:
case 940165:
case 940166:
case 940167:
case 940184:
case 940185:
case 940186:
case 940187:
case 940188:
case 940189:
case 940190:
case 940191:
case 940192:
case 940193:
case 940194:
case 940195:
case 940196:
case 940197:
case 940198:
case 940199:
case 940208:
case 940209:
case 940210:
case 940211:
case 940212:
case 940213:
case 940214:
case 940215:
case 940216:
case 940217:
case 940218:
case 940219:
case 940220:
case 940221:
case 940222:
case 940223:
case 940224:
case 940225:
case 940226:
case 940227:
case 940228:
case 940229:
case 940230:
case 940231:
case 940232:
case 940233:
case 940234:
case 940235:
case 940236:
case 940237:
case 940238:
case 940239:
case 940240:
case 940241:
case 940242:
case 940243:
case 940244:
case 940245:
case 940246:
case 940247:
case 940248:
case 940249:
case 940250:
case 940251:
case 940252:
case 940253:
case 940254:
case 940255:
case 940256:
case 940257:
case 940258:
case 940259:
case 940260:
case 940261:
case 940262:
case 940263:
case 940264:
case 940265:
case 940266:
case 940267:
case 940268:
case 940269:
case 940270:
case 940271:
case 940272:
case 940273:
case 940274:
case 940275:
case 940276:
case 940277:
case 940278:
case 940279:
case 940280:
case 940281:
case 940282:
case 940283:
case 940284:
case 940285:
case 940286:
case 940287:
case 940312:
case 940313:
case 940314:
case 940315:
case 940316:
case 940317:
case 940318:
case 940319:
case 940320:
case 940321:
case 940322:
case 940323:
case 940324:
case 940325:
case 940326:
case 940327:
case 940328:
case 940329:
case 940330:
case 940331:
case 940332:
case 940333:
case 940334:
case 940335:
case 940336:
case 940337:
case 940338:
case 940339:
case 940340:
case 940341:
case 940342:
case 940343:
case 940344:
case 940345:
case 940346:
case 940347:
case 940348:
case 940349:
case 940350:
case 940351:
case 940360:
case 940361:
case 940362:
case 940363:
case 940364:
case 940365:
case 940366:
case 940367:
case 940368:
case 940369:
case 940370:
case 940371:
case 940372:
case 940373:
case 940374:
case 940375:
case 940384:
case 940385:
case 940386:
case 940387:
case 940388:
case 940389:
case 940390:
case 940391:
case 940400:
case 940401:
case 940402:
case 940403:
case 940404:
case 940405:
case 940406:
case 940407:
case 940408:
case 940409:
case 940410:
case 940411:
case 940412:
case 940413:
case 940414:
case 940415:
case 940416:
case 940417:
case 940418:
case 940419:
case 940420:
case 940421:
case 940422:
case 940423:
case 940424:
case 940425:
case 940426:
case 940427:
case 940428:
case 940429:
case 940430:
case 940431:
case 940456:
case 940457:
case 940458:
case 940459:
case 940460:
case 940461:
case 940462:
case 940463:
case 940464:
case 940465:
case 940466:
case 940467:
case 940468:
case 940469:
case 940470:
case 940471:
case 940472:
case 940473:
case 940474:
case 940475:
case 940476:
case 940477:
case 940478:
case 940479:
case 940480:
case 940481:
case 940482:
case 940483:
case 940484:
case 940485:
case 940486:
case 940487:
case 940496:
case 940497:
case 940498:
case 940499:
case 940500:
case 940501:
case 940502:
case 940503:
case 940504:
case 940505:
case 940506:
case 940507:
case 940508:
case 940509:
case 940510:
case 940511:
case 940512:
case 940513:
case 940514:
case 940515:
case 940516:
case 940517:
case 940518:
case 940519:
case 940520:
case 940521:
case 940522:
case 940523:
case 940524:
case 940525:
case 940526:
case 940527:
case 940528:
case 940529:
case 940530:
case 940531:
case 940532:
case 940533:
case 940534:
case 940535:
case 940536:
case 940537:
case 940538:
case 940539:
case 940540:
case 940541:
case 940542:
case 940543:
case 940544:
case 940545:
case 940546:
case 940547:
case 940548:
case 940549:
case 940550:
case 940551:
case 940560:
case 940561:
case 940562:
case 940563:
case 940564:
case 940565:
case 940566:
case 940567:
case 940568:
case 940569:
case 940570:
case 940571:
case 940572:
case 940573:
case 940574:
case 940575:
case 940576:
case 940577:
case 940578:
case 940579:
case 940580:
case 940581:
case 940582:
case 940583:
case 940584:
case 940585:
case 940586:
case 940587:
case 940588:
case 940589:
case 940590:
case 940591:
case 940592:
case 940593:
case 940594:
case 940595:
case 940596:
case 940597:
case 940598:
case 940599:
case 940600:
case 940601:
case 940602:
case 940603:
case 940604:
case 940605:
case 940606:
case 940607:
case 940608:
case 940609:
case 940610:
case 940611:
case 940612:
case 940613:
case 940614:
case 940615:
return true; default: return false; } }
}
