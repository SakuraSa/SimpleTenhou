--初始化role
INSERT INTO role (id, name) VALUES (1, '站长');
INSERT INTO role (id, name) VALUES (2, '管理员');
INSERT INTO role (id, name) VALUES (3, '会员');
INSERT INTO role (id, name) VALUES (4, '队长');

--初始化right
INSERT INTO right (id, name) VALUES (0, '管理管理员账户');
INSERT INTO right (id, name) VALUES (1, '管理会员账户');
INSERT INTO right (id, name) VALUES (2, '管理比赛');
INSERT INTO right (id, name) VALUES (3, '上传比赛记录');
INSERT INTO right (id, name) VALUES (4, '发表评论');
INSERT INTO right (id, name) VALUES (5, '上传出场名单');

--初始化各role拥有的right
--游客 无权利
--站长 拥有所有权限
INSERT INTO roleRight (id_role, id_right) VALUES (1, 0);
INSERT INTO roleRight (id_role, id_right) VALUES (1, 1);
INSERT INTO roleRight (id_role, id_right) VALUES (1, 2);
INSERT INTO roleRight (id_role, id_right) VALUES (1, 3);
INSERT INTO roleRight (id_role, id_right) VALUES (1, 4);
INSERT INTO roleRight (id_role, id_right) VALUES (1, 5);
--管理员 拥有除了0以外的权限
INSERT INTO roleRight (id_role, id_right) VALUES (2, 1);
INSERT INTO roleRight (id_role, id_right) VALUES (2, 2);
INSERT INTO roleRight (id_role, id_right) VALUES (2, 3);
INSERT INTO roleRight (id_role, id_right) VALUES (2, 4);
INSERT INTO roleRight (id_role, id_right) VALUES (2, 5);
--会员 发表评论的权限
INSERT INTO roleRight (id_role, id_right) VALUES (3, 4);
--队员 上传记录和发表评论的权限
INSERT INTO roleRight (id_role, id_right) VALUES (4, 3);
INSERT INTO roleRight (id_role, id_right) VALUES (4, 4);
INSERT INTO roleRight (id_role, id_right) VALUES (4, 5);

--初始化gameStatu
INSERT INTO gameStatue (id, name) VALUES (0, '准备中');
INSERT INTO gameStatue (id, name) VALUES (1, '已开始');
INSERT INTO gameStatue (id, name) VALUES (2, '已结束');

--name    : admin
--password: admin        (while salt is rnd495)
INSERT INTO user (name, password, id_role) 
VALUES (
    'admin', 
    '916b08734c2c8295b523b4f7d95821b3726d9dc13b9e31f889808d41486e5d64',
    1);

